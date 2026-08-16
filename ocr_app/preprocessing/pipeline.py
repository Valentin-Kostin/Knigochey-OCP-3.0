"""
Конвейер предобработки для OCR.
Объединяет несколько процессоров изображений в цепочку.
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
    OrientationProcessor,
    ContrastProcessor,
    ProcessorConfig,
)


@dataclass
class PipelineConfig:
    """Конфигурация конвейера предобработки."""
    
    denoise: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=False))
    clahe: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=True))
    orientation: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=True))
    deskew: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=False))
    contrast: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=True))
    binarization: ProcessorConfig = field(default_factory=lambda: ProcessorConfig(enabled=False))
    
    @classmethod
    def default(cls) -> "PipelineConfig":
        """Получить конфигурацию по умолчанию для исторических документов."""
        return cls(
            denoise=ProcessorConfig(enabled=False),
            clahe=ProcessorConfig(enabled=True, parameters={"clip_limit": 2.0}),
            orientation=ProcessorConfig(enabled=True),
            deskew=ProcessorConfig(enabled=True, parameters={"limit": 5.0}),
            contrast=ProcessorConfig(enabled=True, parameters={"factor": 1.2}),
            binarization=ProcessorConfig(enabled=False),
        )
    
    @classmethod
    def for_old_printed(cls) -> "PipelineConfig":
        """Конфигурация, оптимизированная для старых печатных текстов."""
        return cls(
            denoise=ProcessorConfig(enabled=True, parameters={"method": "bilateral", "strength": 5}),
            clahe=ProcessorConfig(enabled=True, parameters={"clip_limit": 3.0}),
            orientation=ProcessorConfig(enabled=True),
            deskew=ProcessorConfig(enabled=True),
            contrast=ProcessorConfig(enabled=True, parameters={"factor": 1.5}),
            binarization=ProcessorConfig(enabled=False),
        )
    
    @classmethod
    def for_handwritten(cls) -> "PipelineConfig":
        """Конфигурация, оптимизированная для рукописных манускриптов."""
        return cls(
            denoise=ProcessorConfig(enabled=True, parameters={"method": "nlmeans", "strength": 8}),
            clahe=ProcessorConfig(enabled=True, parameters={"clip_limit": 2.5}),
            orientation=ProcessorConfig(enabled=True),
            deskew=ProcessorConfig(enabled=True, parameters={"limit": 10.0}),
            contrast=ProcessorConfig(enabled=True, parameters={"factor": 1.3}),
            binarization=ProcessorConfig(enabled=False),
        )
    
    @classmethod
    def for_low_quality(cls) -> "PipelineConfig":
        """Конфигурация для сканов низкого качества."""
        return cls(
            denoise=ProcessorConfig(enabled=True, parameters={"method": "nlmeans", "strength": 15}),
            clahe=ProcessorConfig(enabled=True, parameters={"clip_limit": 4.0}),
            orientation=ProcessorConfig(enabled=True),
            deskew=ProcessorConfig(enabled=True, parameters={"limit": 15.0}),
            contrast=ProcessorConfig(enabled=True, parameters={"factor": 1.8, "brightness": 10}),
            binarization=ProcessorConfig(enabled=True, parameters={"method": "adaptive"}),
        )


class PreprocessingPipeline:
    """
    Конвейер для объединения операций предобработки изображений.
    
    Применяет процессоры в определённом порядке для оптимизации изображений для OCR.
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Инициализировать конвейер предобработки.
        
        Args:
            config: Конфигурация конвейера. Используется по умолчанию, если None.
        """
        self.config = config or PipelineConfig.default()
        self._processors: list[ImageProcessor] = []
        self._build_pipeline()
    
    def _build_pipeline(self) -> None:
        """Построить цепочку процессоров на основе конфигурации."""
        self._processors = []
        
        # Порядок важен: сначала ориентация, потом шумоподавление, затем улучшения, потом бинаризация
        if self.config.orientation.enabled:
            self._processors.append(OrientationProcessor(self.config.orientation))
        
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
        Обработать изображение через конвейер.
        
        Args:
            image: Входное PIL Image.
            
        Returns:
            Обработанное PIL Image.
        """
        result = image
        
        for processor in self._processors:
            result = processor.apply(result)
        
        return result
    
    def process_file(self, input_path: Path, output_path: Optional[Path] = None) -> Image.Image:
        """
        Обработать файл изображения.
        
        Args:
            input_path: Путь к входному файлу изображения.
            output_path: Опциональный путь для сохранения обработанного изображения.
            
        Returns:
            Обработанное PIL Image.
            
        Raises:
            FileNotFoundError: Если входной файл не существует.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Файл изображения не найден: {input_path}")
        
        # Загрузить изображение
        with Image.open(input_path) as img:
            # Конвертировать в RGB при необходимости
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Обработать
            result = self.process(img)
        
        # Сохранить, если указан путь вывода
        if output_path is not None:
            result.save(output_path)
        
        return result
    
    def get_active_processors(self) -> list[str]:
        """Получить список имён активных процессоров."""
        return [p.name for p in self._processors]
    
    def rebuild(self, config: Optional[PipelineConfig] = None) -> None:
        """
        Перестроить конвейер с новой конфигурацией.
        
        Args:
            config: Новая конфигурация конвейера.
        """
        if config is not None:
            self.config = config
        self._build_pipeline()
