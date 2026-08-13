"""
OCR Engine module for historical Slavic text recognition.
Supports multiple engines: Tesseract, Kraken, and TrOCR-based models.
"""

from .base import OCREngine, OCRResult
from .tesseract_engine import TesseractEngine
from .kraken_engine import KrakenEngine
from .trocr_engine import TrOCREngine

__all__ = [
    "OCREngine",
    "OCRResult",
    "TesseractEngine",
    "KrakenEngine",
    "TrOCREngine",
]
