"""
Tesseract OCR engine implementation.
Uses pytesseract for Python bindings to Tesseract OCR.
"""

import time
from pathlib import Path
from typing import Optional

from .base import OCREngine, OCRResult


class TesseractEngine(OCREngine):
    """Tesseract OCR engine for historical Slavic text recognition."""
    
    # Supported languages for Slavic texts
    SLAVIC_LANGS = {
        "rus": "Russian",
        "ukr": "Ukrainian",
        "bul": "Bulgarian",
        "srp": "Serbian",
        "mkd": "Macedonian",
        "bel": "Belarusian",
        "pol": "Polish",
        "ces": "Czech",
        "slk": "Slovak",
        "hrv": "Croatian",
        "slv": "Slovenian",
    }
    
    def __init__(self):
        """Initialize Tesseract engine."""
        super().__init__("Tesseract OCR")
        self._tesseract_langs: list[str] = []
    
    def _check_availability(self) -> None:
        """Check if Tesseract is installed and available."""
        try:
            import pytesseract
            from PIL import Image
            
            # Get available languages
            self._tesseract_langs = pytesseract.get_languages(config='')
            
            # Check if at least one Slavic language is available
            available_slavic = [
                lang for lang in self.SLAVIC_LANGS.keys() 
                if lang in self._tesseract_langs
            ]
            
            self.is_available = len(available_slavic) > 0 or 'eng' in self._tesseract_langs
            
        except (ImportError, RuntimeError):
            self.is_available = False
    
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Perform OCR using Tesseract.
        
        Args:
            image_path: Path to the image file.
            model_name: Language code(s) to use (e.g., 'rus', 'rus+eng').
                       If None, tries to auto-detect available Slavic languages.
            
        Returns:
            OCRResult with recognized text.
        """
        if not self.is_available:
            raise RuntimeError("Tesseract OCR is not available")
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        start_time = time.time()
        
        try:
            import pytesseract
            from PIL import Image
            
            # Determine language
            if model_name is None:
                # Auto-select first available Slavic language or English
                slavic_available = [
                    lang for lang in self.SLAVIC_LANGS.keys() 
                    if lang in self._tesseract_langs
                ]
                if slavic_available:
                    lang = slavic_available[0]
                else:
                    lang = 'eng'
            else:
                lang = model_name
            
            # Open image and perform OCR
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                config = f"--oem 3 --psm 6 -l {lang}"
                text = pytesseract.image_to_string(img, config=config)
                
                # Get confidence data
                data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
                
                # Calculate average confidence
                confidences = [c for c in data['conf'] if c > -1]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = (time.time() - start_time) * 1000  # ms
            
            warnings = []
            if avg_confidence < 50:
                warnings.append("Low confidence score - result may be inaccurate")
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100.0,
                engine_name=self.name,
                model_name=lang,
                processing_time_ms=processing_time,
                warnings=warnings,
                metadata={
                    "tesseract_version": pytesseract.get_tesseract_version(),
                    "languages_used": lang,
                }
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return OCRResult(
                text="",
                confidence=0.0,
                engine_name=self.name,
                processing_time_ms=processing_time,
                warnings=[f"OCR failed: {str(e)}"],
                metadata={"error": str(e)}
            )
    
    def get_available_models(self) -> list[str]:
        """Get list of available Tesseract languages."""
        if not self.is_available:
            return []
        
        # Return Slavic languages that are available, plus English
        available = []
        for lang_code, lang_name in self.SLAVIC_LANGS.items():
            if lang_code in self._tesseract_langs:
                available.append(f"{lang_code} ({lang_name})")
        
        if 'eng' in self._tesseract_langs and 'eng' not in [l.split()[0] for l in available]:
            available.append("eng (English)")
        
        return available if available else ["No Slavic languages installed"]
