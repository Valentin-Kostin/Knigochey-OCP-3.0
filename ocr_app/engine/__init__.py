"""
Модуль OCR-движков для распознавания исторических славянских текстов.
Поддерживает несколько движков: Tesseract, Kraken, TrOCR и CSLAV.
"""

from .base import OCREngine, OCRResult
from .tesseract_engine import TesseractEngine
from .kraken_engine import KrakenEngine
from .trocr_engine import TrOCREngine
from .cslav_engine import CSLAVEngine

__all__ = [
    "OCREngine",
    "OCRResult",
    "TesseractEngine",
    "KrakenEngine",
    "TrOCREngine",
    "CSLAVEngine",
]
