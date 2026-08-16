"""
Реализация OCR-движка на базе TrOCR.
Использует модели-трансформеры для продвинутого распознавания текста.
"""

import time
from pathlib import Path
from typing import Optional

from .base import OCREngine, OCRResult


class TrOCREngine(OCREngine):
    """Движок TrOCR для продвинутого распознавания исторических текстов с использованием трансформеров."""
    
    # Предобученные модели TrOCR
    MODELS = {
        "trocr-small-printed": "Малая модель для печатного текста (быстрее, менее точная)",
        "trocr-base-printed": "Базовая модель для печатного текста (сбалансированная)",
        "trocr-large-printed": "Большая модель для печатного текста (медленнее, более точная)",
        "trocr-small-handwritten": "Малая модель для рукописного текста",
        "trocr-base-handwritten": "Базовая модель для рукописного текста",
    }
    
    def __init__(self):
        """Инициализировать движок TrOCR."""
        super().__init__("TrOCR (Transformers)")
        self._model_cache: dict = {}
        self._preferred_device: str = "auto"  # "auto", "cpu", или "cuda"
    
    def _check_availability(self) -> None:
        """Проверить доступность необходимых библиотек transformers."""
        try:
            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            
            # Проверить доступность CUDA
            self.cuda_available = torch.cuda.is_available()
            
            # Использовать предпочтительное устройство, если задано
            if self._preferred_device == "cuda" and self.cuda_available:
                self.device = "cuda"
            elif self._preferred_device == "cpu":
                self.device = "cpu"
            else:  # "auto" или по умолчанию
                self.device = "cuda" if self.cuda_available else "cpu"
            
            self.is_available = True
            
        except ImportError:
            self.is_available = False
            self.cuda_available = False
            self.device = "cpu"
    
    def set_device(self, device: str) -> None:
        """
        Установить предпочтительное устройство для вычислений.
        
        Args:
            device: "cpu", "cuda", или "auto" для автоматического выбора.
        """
        self._preferred_device = device
        # Перебросить флаг доступности, чтобы проверка выполнилась снова с новым устройством
        self._availability_checked = False
    
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Выполнить OCR с помощью TrOCR.
        
        Args:
            image_path: Путь к файлу изображения.
            model_name: Название модели из Hugging Face. 
                       Если None, использует 'trocr-base-printed'.
            
        Returns:
            OCRResult с распознанным текстом.
        """
        if not self.is_available:
            raise RuntimeError(
                "TrOCR недоступен. Установите: pip install transformers torch torchvision"
            )
        
        if not image_path.exists():
            raise FileNotFoundError(f"Файл изображения не найден: {image_path}")
        
        start_time = time.time()
        
        try:
            import torch
            from PIL import Image
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            
            # Модель по умолчанию
            if model_name is None:
                model_name = "microsoft/trocr-base-printed"
            elif not model_name.startswith("microsoft/"):
                model_name = f"microsoft/{model_name}"
            
            # Загрузить или получить из кэша
            cache_key = model_name
            if cache_key not in self._model_cache:
                processor = TrOCRProcessor.from_pretrained(model_name)
                model = VisionEncoderDecoderModel.from_pretrained(model_name)
                model.to(self.device)
                model.eval()
                self._model_cache[cache_key] = (processor, model)
            
            processor, model = self._model_cache[cache_key]
            
            # Открыть и предобработать изображение
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Обработать изображение
                pixel_values = processor(images=img, return_tensors="pt").pixel_values
                pixel_values = pixel_values.to(self.device)
                
                # Сгенерировать текст
                with torch.no_grad():
                    generated_ids = model.generate(pixel_values)
                
                # Декодировать
                generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            processing_time = (time.time() - start_time) * 1000  # мс
            
            # Оценить уверенность на основе длины текста и генерации
            # TrOCR не предоставляет прямых показателей уверенности
            confidence = 0.75  # Умеренная уверенность по умолчанию
            if len(generated_text.strip()) == 0:
                confidence = 0.0
                warnings = ["Текст не был распознан"]
            elif len(generated_text.strip()) < 10:
                confidence = 0.5
                warnings = ["Распознан очень короткий текст — может быть неполным"]
            else:
                warnings = []
            
            return OCRResult(
                text=generated_text.strip(),
                confidence=confidence,
                engine_name=self.name,
                model_name=model_name.split('/')[-1],
                processing_time_ms=processing_time,
                warnings=warnings,
                metadata={
                    "device": self.device,
                    "cuda_available": self.cuda_available,
                    "model_full_name": model_name,
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
        """Получить список доступных моделей TrOCR."""
        if not self.is_available:
            return []
        
        return list(self.MODELS.keys())
    
    def get_model_description(self, model_name: str) -> str:
        """
        Получить описание модели.
        
        Args:
            model_name: Название модели.
            
        Returns:
            Строка описания.
        """
        # Сначала попробовать точное совпадение
        if model_name in self.MODELS:
            return self.MODELS[model_name]
        
        # Попробовать без префикса
        for key, value in self.MODELS.items():
            if key.endswith(model_name) or model_name.endswith(key):
                return value
        
        return "Пользовательская или неизвестная модель"
    
    def clear_cache(self) -> None:
        """Очистить кэш моделей для освобождения памяти."""
        import torch
        
        self._model_cache.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
