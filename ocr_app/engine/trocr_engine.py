"""
TrOCR-based OCR engine implementation.
Uses transformer models for advanced text recognition.
"""

import time
from pathlib import Path
from typing import Optional

from .base import OCREngine, OCRResult


class TrOCREngine(OCREngine):
    """TrOCR engine for advanced historical text recognition using transformers."""
    
    # Pre-trained TrOCR models
    MODELS = {
        "trocr-small-printed": "Small model for printed text (faster, less accurate)",
        "trocr-base-printed": "Base model for printed text (balanced)",
        "trocr-large-printed": "Large model for printed text (slower, more accurate)",
        "trocr-small-handwritten": "Small model for handwritten text",
        "trocr-base-handwritten": "Base model for handwritten text",
    }
    
    def __init__(self):
        """Initialize TrOCR engine."""
        super().__init__("TrOCR (Transformers)")
        self._model_cache: dict = {}
    
    def _check_availability(self) -> None:
        """Check if required transformers libraries are available."""
        try:
            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            
            # Check CUDA availability
            self.cuda_available = torch.cuda.is_available()
            self.device = "cuda" if self.cuda_available else "cpu"
            
            self.is_available = True
            
        except ImportError:
            self.is_available = False
            self.cuda_available = False
            self.device = "cpu"
    
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Perform OCR using TrOCR.
        
        Args:
            image_path: Path to the image file.
            model_name: Model name from Hugging Face. 
                       If None, uses 'trocr-base-printed'.
            
        Returns:
            OCRResult with recognized text.
        """
        if not self.is_available:
            raise RuntimeError(
                "TrOCR is not available. Install with: pip install transformers torch torchvision"
            )
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        start_time = time.time()
        
        try:
            import torch
            from PIL import Image
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            
            # Default model
            if model_name is None:
                model_name = "microsoft/trocr-base-printed"
            elif not model_name.startswith("microsoft/"):
                model_name = f"microsoft/{model_name}"
            
            # Load or get from cache
            cache_key = model_name
            if cache_key not in self._model_cache:
                processor = TrOCRProcessor.from_pretrained(model_name)
                model = VisionEncoderDecoderModel.from_pretrained(model_name)
                model.to(self.device)
                model.eval()
                self._model_cache[cache_key] = (processor, model)
            
            processor, model = self._model_cache[cache_key]
            
            # Open and preprocess image
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Process image
                pixel_values = processor(images=img, return_tensors="pt").pixel_values
                pixel_values = pixel_values.to(self.device)
                
                # Generate text
                with torch.no_grad():
                    generated_ids = model.generate(pixel_values)
                
                # Decode
                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            processing_time = (time.time() - start_time) * 1000  # ms
            
            # Estimate confidence based on text length and generation
            # TrOCR doesn't provide direct confidence scores
            confidence = 0.75  # Default moderate confidence
            if len(generated_text.strip()) == 0:
                confidence = 0.0
                warnings = ["No text was recognized"]
            elif len(generated_text.strip()) < 10:
                confidence = 0.5
                warnings = ["Very short text recognized - may be incomplete"]
            else:
                warnings = []
            
            return OCRResult(
                text=generated_text.strip(),
                confidence=confidence,
                engine_name=self.name,
                model_name=model_name.split('/')[-1],
                processing_time_ms=processing_time,
                warnings=warnings,
                metadata={
                    "device": self.device,
                    "cuda_available": self.cuda_available,
                    "model_full_name": model_name,
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
        """Get list of available TrOCR models."""
        if not self.is_available:
            return []
        
        return list(self.MODELS.keys())
    
    def get_model_description(self, model_name: str) -> str:
        """
        Get description of a model.
        
        Args:
            model_name: Name of the model.
            
        Returns:
            Description string.
        """
        # Try exact match first
        if model_name in self.MODELS:
            return self.MODELS[model_name]
        
        # Try without prefix
        for key, value in self.MODELS.items():
            if key.endswith(model_name) or model_name.endswith(key):
                return value
        
        return "Custom or unknown model"
    
    def clear_cache(self) -> None:
        """Clear cached models to free memory."""
        import torch
        
        self._model_cache.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
