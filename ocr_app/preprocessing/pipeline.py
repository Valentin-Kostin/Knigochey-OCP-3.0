"""
Preprocessing pipeline for OCR.
Chains multiple image processors together.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image

from .processors import (
    ImageProcessor,
    DenoiseProcessor,
    BinarizationProcessor,
    CLAHEProcessor,
    DeskewProcessor,
    ContrastProcessor,
    ProcessorConfig,
)


@dataclass
class PipelineConfig:
    """Configuration for the preprocessing pipeline."""
    
    denoise: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=False))
    clahe: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=True))
    deskew: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=False))
    contrast: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=True))
    binarization: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=False))
    
    @classmethod
    def default(cls) -> "PipelineConfig":
        """Get default configuration for historical documents."""
        return cls(
            denoise=ProcessorConfig(enabled=False),
            clahe=ProcessorConfig(enabled=True, parameters={"clip_limit": 2.0}),
            deskew=ProcessorConfig(enabled=False),
            contrast=ProcessorConfig(enabled=True, parameters={"factor": 1.2}),
            binarization=ProcessorConfig(enabled=False),
        )
    
    @classmethod
    def for_old_printed(cls) -> "PipelineConfig":
        """Configuration optimized for old printed texts."""
        return cls(
            denoise=ProcessorConfig(enabled=True, parameters={"method": "bilateral", "strength": 5}),
            clahe=ProcessorConfig(enabled=True, parameters={"clip_limit": 3.0}),
            deskew=ProcessorConfig(enabled=True),
            contrast=ProcessorConfig(enabled=True, parameters={"factor": 1.5}),
            binarization=ProcessorConfig(enabled=False),
        )
    
    @classmethod
    def for_handwritten(cls) -> "PipelineConfig":
        """Configuration optimized for handwritten manuscripts."""
        return cls(
            denoise=ProcessorConfig(enabled=True, parameters={"method": "nlmeans", "strength": 8}),
            clahe=ProcessorConfig(enabled=True, parameters={"clip_limit": 2.5}),
            deskew=ProcessorConfig(enabled=True, parameters={"limit": 10.0}),
            contrast=ProcessorConfig(enabled=True, parameters={"factor": 1.3}),
            binarization=ProcessorConfig(enabled=False),
        )
    
    @classmethod
    def for_low_quality(cls) -> "PipelineConfig":
        """Configuration for low quality scans."""
        return cls(
            denoise=ProcessorConfig(enabled=True, parameters={"method": "nlmeans", "strength": 15}),
            clahe=ProcessorConfig(enabled=True, parameters={"clip_limit": 4.0}),
            deskew=ProcessorConfig(enabled=True, parameters={"limit": 15.0}),
            contrast=ProcessorConfig(enabled=True, parameters={"factor": 1.8, "brightness": 10}),
            binarization=ProcessorConfig(enabled=True, parameters={"method": "adaptive"}),
        )


class PreprocessingPipeline:
    """
    Pipeline for chaining image preprocessing operations.
    
    Applies processors in a specific order to optimize images for OCR.
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the preprocessing pipeline.
        
        Args:
            config: Pipeline configuration. Uses default if None.
        """
        self.config = config or PipelineConfig.default()
        self._processors: list[ImageProcessor] = []
        self._build_pipeline()
    
    def _build_pipeline(self) -> None:
        """Build the processor chain based on configuration."""
        self._processors = []
        
        # Order matters: denoise first, then enhancements, then binarization
        if self.config.denoise.enabled:
            self._processors.append(DenoiseProcessor(self.config.denoise))
        
        if self.config.clahe.enabled:
            self._processors.append(CLAHEProcessor(self.config.clahe))
        
        if self.config.deskew.enabled:
            self._processors.append(DeskewProcessor(self.config.deskew))
        
        if self.config.contrast.enabled:
            self._processors.append(ContrastProcessor(self.config.contrast))
        
        if self.config.binarization.enabled:
            self._processors.append(BinarizationProcessor(self.config.binarization))
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Process an image through the pipeline.
        
        Args:
            image: Input PIL Image.
            
        Returns:
            Processed PIL Image.
        """
        result = image
        
        for processor in self._processors:
            result = processor.apply(result)
        
        return result
    
    def process_file(self, input_path: Path, output_path: Optional[Path] = None) -> Image.Image:
        """
        Process an image file.
        
        Args:
            input_path: Path to input image file.
            output_path: Optional path to save processed image.
            
        Returns:
            Processed PIL Image.
            
        Raises:
            FileNotFoundError: If input file doesn't exist.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Image file not found: {input_path}")
        
        # Load image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Process
            result = self.process(img)
        
        # Save if output path specified
        if output_path is not None:
            result.save(output_path)
        
        return result
    
    def get_active_processors(self) -> list[str]:
        """Get list of active processor names."""
        return [p.name for p in self._processors]
    
    def rebuild(self, config: Optional[PipelineConfig] = None) -> None:
        """
        Rebuild the pipeline with new configuration.
        
        Args:
            config: New pipeline configuration.
        """
        if config is not None:
            self.config = config
        self._build_pipeline()
