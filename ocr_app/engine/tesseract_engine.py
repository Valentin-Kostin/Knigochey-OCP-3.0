"""
Реализация OCR-движка Tesseract.
Использует pytesseract для Python-привязок к Tesseract OCR.
"""

import time
from pathlib import Path
from typing import Optional

from .base import OCREngine, OCRResult


class TesseractEngine(OCREngine):
    """OCR-движок Tesseract для распознавания исторических славянских текстов."""
    
    # Поддерживаемые языки для славянских текстов
    SLAVIC_LANGS = {
        "rus": "Русский",
        "ukr": "Украинский",
        "bul": "Болгарский",
        "srp": "Сербский",
        "mkd": "Македонский",
        "bel": "Белорусский",
        "pol": "Польский",
        "ces": "Чешский",
        "slk": "Словацкий",
        "hrv": "Хорватский",
        "slv": "Словенский",
    }
    
    def __init__(self, tesseract_path: str = ""):
        """
        Инициализировать движок Tesseract.
        
        Args:
            tesseract_path: Путь к исполняемому файлу tesseract.exe (опционально).
        """
        super().__init__("Tesseract OCR")
        self._tesseract_langs: list[str] = []
        self._tesseract_path = tesseract_path
        
        # Установить путь если указан
        if tesseract_path:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            except Exception:
                pass  # Обработаем при проверке доступности
    
    def _check_availability(self) -> None:
        """Проверить установлен ли Tesseract и доступен ли он."""
        try:
            import pytesseract
            from PIL import Image
            
            # Получить доступные языки
            self._tesseract_langs = pytesseract.get_languages(config='')
            
            # Проверить наличие хотя бы одного славянского языка
            available_slavic = [
                lang for lang in self.SLAVIC_LANGS.keys() 
                if lang in self._tesseract_langs
            ]
            
            self.is_available = len(available_slavic) > 0 or 'eng' in self._tesseract_langs
            
        except (ImportError, RuntimeError, FileNotFoundError):
            self.is_available = False
            self._tesseract_langs = []
    
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Выполнить OCR с помощью Tesseract.
        
        Args:
            image_path: Путь к файлу изображения.
            model_name: Код(ы) языка для использования (например, 'rus', 'rus+eng').
                       Если None, пытается автоматически определить доступные славянские языки.
            
        Returns:
            OCRResult с распознанным текстом.
        """
        if not self.is_available:
            raise RuntimeError("Tesseract OCR недоступен")
        
        if not image_path.exists():
            raise FileNotFoundError(f"Файл изображения не найден: {image_path}")
        
        start_time = time.time()
        
        try:
            import pytesseract
            from PIL import Image
            
            # Определить язык
            if model_name is None:
                # Автовыбор первого доступного славянского языка или английского
                slavic_available = [
                    lang for lang in self.SLAVIC_LANGS.keys() 
                    if lang in self._tesseract_langs
                ]
                if slavic_available:
                    lang = slavic_available[0]
                else:
                    lang = 'eng'
            else:
                lang = model_name
            
            # Открыть изображение и выполнить OCR
            with Image.open(image_path) as img:
                # Конвертировать в RGB при необходимости
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                config = f"--oem 3 --psm 6 -l {lang}"
                text = pytesseract.image_to_string(img, config=config)
                
                # Получить данные об уверенности
                data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
                
                # Вычислить среднюю уверенность
                confidences = [c for c in data['conf'] if c > -1]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            processing_time = (time.time() - start_time) * 1000  # мс
            
            warnings = []
            if avg_confidence < 50:
                warnings.append("Низкий показатель уверенности — результат может быть неточным")
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence / 100.0,
                engine_name=self.name,
                model_name=lang,
                processing_time_ms=processing_time,
                warnings=warnings,
                metadata={
                    "tesseract_version": pytesseract.get_tesseract_version(),
                    "languages_used": lang,
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
        """Получить список доступных языков Tesseract."""
        if not self.is_available:
            return []
        
        # Вернуть доступные славянские языки плюс английский
        available = []
        for lang_code, lang_name in self.SLAVIC_LANGS.items():
            if lang_code in self._tesseract_langs:
                available.append(f"{lang_code} ({lang_name})")
        
        if 'eng' in self._tesseract_langs and 'eng' not in [l.split()[0] for l in available]:
            available.append("eng (English)")
        
        return available if available else ["Славянские языки не установлены"]
