"""
Классы обработки изображений для предобработки OCR.
Реализует различные техники улучшения для исторических документов.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image


@dataclass
class ProcessorConfig:
    """Конфигурация для процессоров изображений."""
    enabled: bool = True
    parameters: dict = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class ImageProcessor(ABC):
    """Абстрактный базовый класс для процессоров изображений."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """
        Инициализировать процессор.
        
        Args:
            config: Конфигурация процессора.
        """
        self.config = config or ProcessorConfig()
        self.name = self.__class__.__name__
    
    @abstractmethod
    def process(self, image: Image.Image) -> Image.Image:
        """
        Обработать изображение.
        
        Args:
            image: Входное PIL Image.
            
        Returns:
            Обработанное PIL Image.
        """
        pass
    
    def apply(self, image: Image.Image) -> Image.Image:
        """
        Применить обработку, если включено.
        
        Args:
            image: Входное PIL Image.
            
        Returns:
            Обработанное или исходное PIL Image.
        """
        if self.config.enabled:
            return self.process(image)
        return image


class DenoiseProcessor(ImageProcessor):
    """Процессор шумоподавления с использованием non-local means или двусторонней фильтрации."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Инициализировать процессор шумоподавления."""
        default_params = {
            "method": "bilateral",  # 'bilateral' или 'nlmeans'
            "strength": 10,
            "template_size": 7,
            "search_window": 21,
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Применить шумоподавление к изображению.
        
        Args:
            image: Входное PIL Image.
            
        Returns:
            Изображение с шумоподавлением PIL Image.
        """
        try:
            import cv2
            
            # Конвертировать в numpy массив
            img_array = np.array(image)
            
            # Конвертировать в BGR для OpenCV, если RGB
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            method = self.config.parameters.get("method", "bilateral")
            strength = self.config.parameters.get("strength", 10)
            
            if method == "bilateral":
                # Двусторонний фильтр — сохраняет края
                d = self.config.parameters.get("template_size", 7)
                sigma_color = strength
                sigma_space = strength
                
                if len(img_array.shape) == 3:
                    processed = cv2.bilateralFilter(img_array, d, sigma_color, sigma_space)
                else:
                    processed = cv2.bilateralFilter(img_array, d, sigma_color, sigma_space)
            
            elif method == "nlmeans":
                # Non-local means шумоподавление
                h = strength
                template_size = self.config.parameters.get("template_size", 7)
                search_window = self.config.parameters.get("search_window", 21)
                
                if len(img_array.shape) == 3:
                    processed = cv2.fastNlMeansDenoisingColored(
                        img_array, None, h, h, template_size, search_window
                    )
                else:
                    processed = cv2.fastNlMeansDenoising(
                        img_array, None, h, template_size, search_window
                    )
            else:
                processed = img_array
            
            # Конвертировать обратно в RGB при необходимости
            if len(processed.shape) == 3 and processed.shape[2] == 3:
                processed = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            
            return Image.fromarray(processed)
            
        except ImportError:
            # OpenCV недоступен, вернуть исходное
            return image
        except Exception:
            # Любая ошибка, вернуть исходное
            return image


class BinarizationProcessor(ImageProcessor):
    """Процессор бинаризации с использованием метода Оцу или адаптивной пороговой обработки."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Инициализировать процессор бинаризации."""
        default_params = {
            "method": "otsu",  # 'otsu', 'adaptive' или 'simple'
            "threshold": 127,
            "block_size": 11,
            "c_value": 2,
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Применить бинаризацию к изображению.
        
        Args:
            image: Входное PIL Image.
            
        Returns:
            Бинаризованное PIL Image.
        """
        try:
            import cv2
            
            # Конвертировать в оттенки серого
            img_array = np.array(image.convert('L'))
            
            method = self.config.parameters.get("method", "otsu")
            
            if method == "otsu":
                # Пороговая обработка Оцу
                _, processed = cv2.threshold(
                    img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
            
            elif method == "adaptive":
                # Адаптивная пороговая обработка
                block_size = self.config.parameters.get("block_size", 11)
                c_value = self.config.parameters.get("c_value", 2)
                
                # Размер блока должен быть нечётным
                if block_size % 2 == 0:
                    block_size += 1
                
                processed = cv2.adaptiveThreshold(
                    img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, block_size, c_value
                )
            
            elif method == "simple":
                # Простая пороговая обработка
                threshold = self.config.parameters.get("threshold", 127)
                _, processed = cv2.threshold(
                    img_array, threshold, 255, cv2.THRESH_BINARY
                )
            else:
                processed = img_array
            
            return Image.fromarray(processed)
            
        except ImportError:
            return image
        except Exception:
            return image


class CLAHEProcessor(ImageProcessor):
    """Процессор ограничения контрастной адаптивной гистограммной эквализации (CLAHE)."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Инициализировать процессор CLAHE."""
        default_params = {
            "clip_limit": 2.0,
            "tile_grid_size": (8, 8),
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Применить CLAHE к изображению.
        
        Args:
            image: Входное PIL Image.
            
        Returns:
            Улучшенное PIL Image.
        """
        try:
            import cv2
            
            # Конвертировать в оттенки серого
            img_array = np.array(image.convert('L'))
            
            clip_limit = self.config.parameters.get("clip_limit", 2.0)
            tile_grid_size = self.config.parameters.get("tile_grid_size", (8, 8))
            
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            processed = clahe.apply(img_array)
            
            return Image.fromarray(processed)
            
        except ImportError:
            return image
        except Exception:
            return image


class DeskewProcessor(ImageProcessor):
    """Процессор исправления перекоса изображения."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Инициализировать процессор исправления перекоса."""
        default_params = {
            "delta": 1.0,
            "limit": 5.0,  # Максимальный угол поворота в градусах
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Исправить перекос изображения путём обнаружения и коррекции поворота.
        
        Args:
            image: Входное PIL Image.
            
        Returns:
            Исправленное PIL Image.
        """
        try:
            import cv2
            
            # Конвертировать в оттенки серого
            img_array = np.array(image.convert('L'))
            
            limit = self.config.parameters.get("limit", 5.0)
            
            # Вычислить угол перекоса используя моменты
            coords = np.column_stack(np.where(img_array > 0))
            
            if len(coords) == 0:
                return image
            
            angle = cv2.minAreaRect(coords)[-1]
            
            # Скорректировать угол на основе квадранта
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Ограничить угол поворота
            if abs(angle) > limit:
                angle = limit if angle > 0 else -limit
            
            # Пропустить, если угол слишком мал
            if abs(angle) < 0.1:
                return image
            
            # Повернуть изображение
            (h, w) = img_array.shape[:2]
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            processed = cv2.warpAffine(
                img_array, matrix, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            return Image.fromarray(processed)
            
        except ImportError:
            return image
        except Exception:
            return image


class ContrastProcessor(ImageProcessor):
    """Простой процессор улучшения контраста."""
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """Инициализировать процессор контраста."""
        default_params = {
            "factor": 1.2,  # Фактор контраста (>1 увеличивает контраст)
            "brightness": 0,  # Регулировка яркости
        }
        if config is None:
            config = ProcessorConfig(parameters=default_params)
        elif config.parameters is None:
            config.parameters = default_params
        else:
            config.parameters = {**default_params, **config.parameters}
        
        super().__init__(config)
    
    def process(self, image: Image.Image) -> Image.Image:
        """
        Улучшить контраст изображения.
        
        Args:
            image: Входное PIL Image.
            
        Returns:
            Улучшенное PIL Image.
        """
        from PIL import ImageEnhance
        
        factor = self.config.parameters.get("factor", 1.2)
        brightness = self.config.parameters.get("brightness", 0)
        
        # Применить улучшение контраста
        enhancer = ImageEnhance.Contrast(image)
        enhanced = enhancer.enhance(factor)
        
        # Применить улучшение яркости
        if brightness != 0:
            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(1.0 + brightness / 100.0)
        
        return enhanced
