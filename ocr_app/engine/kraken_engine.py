"""
Kraken OCR engine implementation.
Specialized OCR for historical documents and non-Latin scripts.
"""

import time
from pathlib import Path
from typing import Optional

from .base import OCREngine, OCRResult


class KrakenEngine(OCREngine):
    """Kraken OCR engine for historical Slavic manuscript recognition."""
    
    # Pre-trained models suitable for Slavic historical texts
    AVAILABLE_MODELS = {
        "default": "Default model for Latin script",
        "fraktur": "Fraktur model for German historical prints",
        "arabic": "Arabic script model",
    }
    
    def __init__(self):
        """Initialize Kraken engine."""
        super().__init__("Kraken OCR")
        self._installed_models: list[str] = []
    
    def _check_availability(self) -> None:
        """Check if Kraken is installed and available."""
        try:
            import kraken
            
            # Try to get version to verify installation
            self._kraken_version = kraken.__version__
            
            # List installed models (this may fail if no models installed)
            try:
                from kraken import models
                self._installed_models = ["default"]  # Assume default is available
            except Exception:
                self._installed_models = []
            
            self.is_available = True
            
        except ImportError:
            self.is_available = False
            self._kraken_version = None
    
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Perform OCR using Kraken.
        
        Args:
            image_path: Path to the image file.
            model_name: Model name to use. If None, uses default model.
            
        Returns:
            OCRResult with recognized text.
        """
        if not self.is_available:
            raise RuntimeError("Kraken OCR is not available. Install with: pip install kraken")
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        start_time = time.time()
        
        try:
            from kraken import rpred
            from kraken.lib.models import load_model
            from PIL import Image
            
            # Use default model if none specified
            if model_name is None or model_name == "default":
                # Load default model
                try:
                    model = load_model('default')
                    actual_model = "default"
                except Exception:
                    # If default model not available, create minimal result
                    processing_time = (time.time() - start_time) * 1000
                    return OCRResult(
                        text="",
                        confidence=0.0,
                        engine_name=self.name,
                        model_name="default",
                        processing_time_ms=processing_time,
                        warnings=["No Kraken models available. Please train or download a model."],
                        metadata={"error": "No models available"}
                    )
            else:
                # Try to load custom model
                try:
                    model_path = Path(model_name)
                    if model_path.exists():
                        model = load_model(str(model_path))
                        actual_model = model_path.name
                    else:
                        raise FileNotFoundError(f"Model file not found: {model_name}")
                except Exception as e:
                    processing_time = (time.time() - start_time) * 1000
                    return OCRResult(
                        text="",
                        confidence=0.0,
                        engine_name=self.name,
                        processing_time_ms=processing_time,
                        warnings=[f"Failed to load model: {str(e)}"],
                        metadata={"error": str(e)}
                    )
            
            # Open image
            with Image.open(image_path) as img:
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Create predictor
                predictor = rpred.rpred(model, img)
                
                # Extract text
                lines = []
                confidences = []
                
                for record in predictor:
                    line_text = record.prediction
                    line_conf = record.confidence if hasattr(record, 'confidence') else 0.5
                    lines.append(line_text)
                    confidences.append(line_conf)
                
                text = "\n".join(lines)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = (time.time() - start_time) * 1000  # ms
            
            warnings = []
            if avg_confidence < 0.5:
                warnings.append("Low confidence score - result may be inaccurate")
            if not self._installed_models:
                warnings.append("Using default model. Consider training a custom model for better results.")
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                engine_name=self.name,
                model_name=actual_model,
                processing_time_ms=processing_time,
                warnings=warnings,
                metadata={
                    "kraken_version": getattr(self, '_kraken_version', 'unknown'),
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
        """Get list of available Kraken models."""
        if not self.is_available:
            return []
        
        models_list = list(self.AVAILABLE_MODELS.keys())
        if self._installed_models:
            return self._installed_models
        return models_list
    
    def get_model_description(self, model_name: str) -> str:
        """
        Get description of a model.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            Description string.
        """
        return self.AVAILABLE_MODELS.get(model_name, "Unknown model")
