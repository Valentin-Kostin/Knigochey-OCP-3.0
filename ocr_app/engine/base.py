"""
Base classes for OCR engines.
Defines the interface that all OCR engines must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class OCRResult:
    """Result of OCR processing."""
    
    text: str
    confidence: float = 0.0
    engine_name: str = ""
    model_name: str = ""
    processing_time_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_formatted_text(self) -> str:
        """Get formatted text with metadata header if present."""
        header_lines = []
        if self.engine_name:
            header_lines.append(f"Engine: {self.engine_name}")
        if self.model_name:
            header_lines.append(f"Model: {self.model_name}")
        if self.confidence > 0:
            header_lines.append(f"Confidence: {self.confidence:.2%}")
        if self.processing_time_ms > 0:
            header_lines.append(f"Processing time: {self.processing_time_ms:.2f}ms")
        
        if header_lines:
            return "\n".join(header_lines) + "\n\n" + self.text
        return self.text


class OCREngine(ABC):
    """Abstract base class for OCR engines."""
    
    def __init__(self, name: str):
        """
        Initialize the OCR engine.
        
        Args:
            name: Human-readable name of the engine.
        """
        self.name = name
        self.is_available = False
        self._check_availability()
    
    @abstractmethod
    def _check_availability(self) -> None:
        """Check if the engine is available and set is_available flag."""
        pass
    
    @abstractmethod
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Perform OCR on an image.
        
        Args:
            image_path: Path to the image file.
            model_name: Optional model name to use (engine-specific).
            
        Returns:
            OCRResult with recognized text and metadata.
            
        Raises:
            FileNotFoundError: If image file doesn't exist.
            RuntimeError: If engine is not available.
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        Get list of available models for this engine.
        
        Returns:
            List of model names.
        """
        pass
    
    def is_ready(self) -> bool:
        """Check if engine is ready to use."""
        return self.is_available
