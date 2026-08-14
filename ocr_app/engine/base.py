"""
Базовые классы для OCR-движков.
Определяет интерфейс, который должны реализовывать все OCR-движки.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class OCRResult:
    """Результат обработки OCR."""
    
    text: str
    confidence: float = 0.0
    engine_name: str = ""
    model_name: str = ""
    processing_time_ms: float = 0.0
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def has_warnings(self) -> bool:
        """Проверить наличие предупреждений."""
        return len(self.warnings) > 0
    
    def get_formatted_text(self) -> str:
        """Получить отформатированный текст с заголовком метаданных (если есть)."""
        header_lines = []
        if self.engine_name:
            header_lines.append(f"Движок: {self.engine_name}")
        if self.model_name:
            header_lines.append(f"Модель: {self.model_name}")
        if self.confidence > 0:
            header_lines.append(f"Уверенность: {self.confidence:.2%}")
        if self.processing_time_ms > 0:
            header_lines.append(f"Время обработки: {self.processing_time_ms:.2f}мс")
        
        if header_lines:
            return "\n".join(header_lines) + "\n\n" + self.text
        return self.text


class OCREngine(ABC):
    """Абстрактный базовый класс для OCR-движков."""
    
    def __init__(self, name: str):
        """
        Инициализировать OCR-движок.
        
        Args:
            name: Человекочитаемое название движка.
        """
        self.name = name
        self.is_available = False
        self._availability_checked = False
        # Не проверяем доступность сразу при инициализации, чтобы приложение могло запуститься
        # Проверка будет выполнена при первом вызове _ensure_availability() или recognize()
    
    def _ensure_availability(self) -> None:
        """Убедиться, что доступность проверена, выполнив проверку если еще не была сделана."""
        if not self._availability_checked:
            self._check_availability()
            self._availability_checked = True
    
    @abstractmethod
    def _check_availability(self) -> None:
        """Проверить доступность движка и установить флаг is_available."""
        pass
    
    @abstractmethod
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Выполнить OCR на изображении.
        
        Args:
            image_path: Путь к файлу изображения.
            model_name: Опциональное имя модели для использования (зависит от движка).
            
        Returns:
            OCRResult с распознанным текстом и метаданными.
            
        Raises:
            FileNotFoundError: Если файл изображения не найден.
            RuntimeError: Если движок недоступен.
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        Получить список доступных моделей для этого движка.
        
        Returns:
            Список названий моделей.
        """
        pass
    
    def _ensure_availability(self) -> None:
        """Убедиться, что доступность проверена, выполнив проверку если еще не была сделана."""
        if not self._availability_checked:
            self._check_availability()
            self._availability_checked = True
    
    def is_ready(self) -> bool:
        """Проверить готовность движка к использованию."""
        self._ensure_availability()
        return self.is_available
