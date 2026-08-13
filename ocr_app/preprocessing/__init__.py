"""
Модуль предобработки изображений для OCR.
Предоставляет различные техники улучшения изображений для исторических документов.
"""

from .processors import (
    ImageProcessor,
    DenoiseProcessor,
    BinarizationProcessor,
    CLAHEProcessor,
    DeskewProcessor,
    ContrastProcessor,
    ProcessorConfig,
)
from .pipeline import PreprocessingPipeline, PipelineConfig

__all__ = [
    "ImageProcessor",
    "DenoiseProcessor",
    "BinarizationProcessor",
    "CLAHEProcessor",
    "DeskewProcessor",
    "ContrastProcessor",
    "ProcessorConfig",
    "PreprocessingPipeline",
    "PipelineConfig",
]
