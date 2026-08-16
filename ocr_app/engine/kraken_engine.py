"""
Реализация OCR-движка Kraken.
Специализированный OCR для исторических документов и не-латинских скриптов.
"""

import time
from pathlib import Path
from typing import Optional

from .base import OCREngine, OCRResult


class KrakenEngine(OCREngine):
    """OCR-движок Kraken для распознавания исторических славянских рукописей."""
    
    # Предобученные модели, подходящие для славянских исторических текстов
    AVAILABLE_MODELS = {
        "default": "Модель по умолчанию для латинского скрипта",
        "fraktur": "Модель Fraktur для немецких исторических печатных текстов",
        "arabic": "Модель для арабского скрипта",
    }
    
    def __init__(self):
        """Инициализировать движок Kraken."""
        super().__init__("Kraken OCR")
        self._installed_models: list[str] = []
    
    def _check_availability(self) -> None:
        """Проверить установлен ли Kraken и доступен ли он."""
        try:
            import kraken
            
            # Попытаться получить версию для проверки установки
            self._kraken_version = getattr(kraken, '__version__', 'unknown')
            
            # Получить список установленных моделей (может завершиться ошибкой, если модели не установлены)
            try:
                from kraken import models
                self._installed_models = ["default"]  # Предполагаем, что default доступен
            except Exception:
                self._installed_models = []
            
            self.is_available = True
            
        except ImportError:
            self.is_available = False
            self._kraken_version = None
    
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Выполнить OCR с помощью Kraken.
        
        Args:
            image_path: Путь к файлу изображения.
            model_name: Имя модели для использования. Если None, использует модель по умолчанию.
            
        Returns:
            OCRResult с распознанным текстом.
        """
        if not self.is_available:
            raise RuntimeError("Kraken OCR недоступен. Установите: pip install kraken")
        
        if not image_path.exists():
            raise FileNotFoundError(f"Файл изображения не найден: {image_path}")
        
        start_time = time.time()
        
        try:
            from kraken import rpred
            from kraken.lib.models import load_model
            from PIL import Image
            
            # Использовать модель по умолчанию, если не указана
            if model_name is None or model_name == "default":
                # Загрузить модель по умолчанию
                try:
                    model = load_model('default')
                    actual_model = "default"
                except Exception:
                    # Если модель по умолчанию недоступна, создать минимальный результат
                    processing_time = (time.time() - start_time) * 1000
                    return OCRResult(
                        text="",
                        confidence=0.0,
                        engine_name=self.name,
                        model_name="default",
                        processing_time_ms=processing_time,
                        warnings=["Модели Kraken недоступны. Пожалуйста, обучите или загрузите модель."],
                        metadata={"error": "Нет доступных моделей"}
                    )
            else:
                # Попытаться загрузить пользовательскую модель
                try:
                    model_path = Path(model_name)
                    if model_path.exists():
                        model = load_model(str(model_path))
                        actual_model = model_path.name
                    else:
                        raise FileNotFoundError(f"Файл модели не найден: {model_name}")
                except Exception as e:
                    processing_time = (time.time() - start_time) * 1000
                    return OCRResult(
                        text="",
                        confidence=0.0,
                        engine_name=self.name,
                        processing_time_ms=processing_time,
                        warnings=[f"Не удалось загрузить модель: {str(e)}"],
                        metadata={"error": str(e)}
                    )
            
            # Открыть изображение
            with Image.open(image_path) as img:
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Создать предиктор
                predictor = rpred.rpred(model, img)
                
                # Извлечь текст
                lines = []
                confidences = []
                
                for record in predictor:
                    line_text = record.prediction
                    line_conf = record.confidence if hasattr(record, 'confidence') else 0.5
                    lines.append(line_text)
                    confidences.append(line_conf)
                
                text = "\n".join(lines)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = (time.time() - start_time) * 1000  # мс
            
            warnings = []
            if avg_confidence < 0.5:
                warnings.append("Низкий показатель уверенности — результат может быть неточным")
            if not self._installed_models:
                warnings.append("Используется модель по умолчанию. Рассмотрите возможность обучения собственной модели для лучших результатов.")
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                engine_name=self.name,
                model_name=actual_model,
                processing_time_ms=processing_time,
                warnings=warnings,
                metadata={
                    "kraken_version": getattr(self, '_kraken_version', 'unknown'),
                }
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return OCRResult(
                text="",
                confidence=0.0,
                engine_name=self.name,
                processing_time_ms=processing_time,
                warnings=[f"OCR не удался: {str(e)}"],
                metadata={"error": str(e)}
            )
    
    def get_available_models(self) -> list[str]:
        """Получить список доступных моделей Kraken."""
        if not self.is_available:
            return []
        
        models_list = list(self.AVAILABLE_MODELS.keys())
        if self._installed_models:
            return self._installed_models
        return models_list
    
    def get_model_description(self, model_name: str) -> str:
        """
        Получить описание модели.
        
        Args:
            model_name: Название модели.
            
        Returns:
            Строка описания.
        """
        return self.AVAILABLE_MODELS.get(model_name, "Неизвестная модель")
