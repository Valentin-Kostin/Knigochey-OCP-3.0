"""
Image preprocessing module for OCR.
Provides various image enhancement techniques for historical documents.
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
