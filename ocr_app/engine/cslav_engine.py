"""
OCR-движок CSLAV для распознавания старославянских текстов.
Использует собственную CNN-модель, обученную на Евангелии 1606 года.
Поддерживает 49 классов символов и специальный декодер кодировок.
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Tuple
import numpy as np

from .base import OCREngine, OCRResult


class CSLAVEngine(OCREngine):
    """OCR-движок CSLAV для распознавания старославянских текстов."""
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Инициализировать движок CSLAV.
        
        Args:
            model_path: Путь к файлу модели (.h5). Если None, использует модель по умолчанию.
        """
        super().__init__("CSLAV OCR")
        # Путь к модели в папке CSLAV_OCR_1.0-main
        default_model_path = Path(__file__).parent.parent.parent / "CSLAV_OCR_1.0-main" / "machine.h5"
        self.model_path = model_path or default_model_path
        self.model = None
        self.predictions_list = None
        self._load_predictions()
        self._check_availability()
    
    def _load_predictions(self) -> None:
        """Загрузить файл соответствий предсказаний и символов."""
        base_path = Path(__file__).parent.parent.parent / "CSLAV_OCR_1.0-main"
        
        # Основной путь: CSLAV_OCR_1.0-main/predictions.txt
        predictions_file = base_path / "predictions.txt"
        
        if predictions_file.exists():
            try:
                with open(predictions_file, 'r', encoding='utf-8') as f:
                    predictions = f.read()
                predictions_list = predictions.split('\n\n')
                for i in range(len(predictions_list)):
                    predictions_list[i] = predictions_list[i].split('\t')
                self.predictions_list = predictions_list
            except Exception:
                self.predictions_list = []
        else:
            # Альтернативный путь в подпапке CSLAV_OCR-main
            alt_predictions_file = base_path / "CSLAV_OCR-main" / "predictions.txt"
            if alt_predictions_file.exists():
                try:
                    with open(alt_predictions_file, 'r', encoding='utf-8') as f:
                        predictions = f.read()
                    predictions_list = predictions.split('\n\n')
                    for i in range(len(predictions_list)):
                        predictions_list[i] = predictions_list[i].split('\t')
                    self.predictions_list = predictions_list
                except Exception:
                    self.predictions_list = []
            else:
                self.predictions_list = []
    
    def _check_availability(self) -> None:
        """Проверить доступность движка и модели."""
        self.is_available = False  # По умолчанию недоступен
        
        try:
            from tensorflow import keras
            
            # Проверить наличие модели
            if not self.model_path.exists():
                return
            
            # Проверить наличие зависимостей
            try:
                import cv2
                import numpy as np
            except ImportError:
                return
            
            # Загрузить модель
            self.model = keras.models.load_model(str(self.model_path))
            self.is_available = True
            
        except ImportError as e:
            # TensorFlow или другие зависимости не установлены
            return
        except Exception as e:
            # Другие ошибки загрузки модели
            return
    
    def recognize(self, image_path: Path, model_name: Optional[str] = None) -> OCRResult:
        """
        Выполнить OCR с помощью CSLAV.
        
        Args:
            image_path: Путь к файлу изображения.
            model_name: Не используется (для совместимости интерфейса).
            
        Returns:
            OCRResult с распознанным текстом.
        """
        if not self.is_available:
            raise RuntimeError("CSLAV OCR недоступен")
        
        if not image_path.exists():
            raise FileNotFoundError(f"Файл изображения не найден: {image_path}")
        
        start_time = time.time()
        
        try:
            # Получить символы
            symbols = self._get_symbols(
                str(image_path), 
                min_h=15, 
                max_h=700, 
                max_w=400
            )
            
            # Получить контуры для определения строк
            boxes = self._get_boxes(str(image_path), min_h=50, max_h=700, max_w=400)
            
            # Найти границы строк
            edges = self._get_edges(boxes, threshn=70)
            
            # Распределить символы по строкам
            rows = self._symbols_to_rows(symbols, edges)
            
            # Собрать текст
            text = ''
            for row in rows:
                text += self._get_raw_str(row, space=50) + '\n'
            
            # Применить декодер кодировок
            text = self._shit2utf8(text)
            
            processing_time = (time.time() - start_time) * 1000  # мс
            
            warnings = []
            if len(symbols) == 0:
                warnings.append("Символы не обнаружены — возможно, изображение слишком низкого качества")
            
            return OCRResult(
                text=text.strip(),
                confidence=0.0,  # CSLAV не предоставляет уверенность
                engine_name=self.name,
                model_name="CSLAV CNN (49 классов)",
                processing_time_ms=processing_time,
                warnings=warnings,
                metadata={
                    "symbols_detected": len(symbols),
                    "rows_detected": len(rows),
                    "model_path": str(self.model_path),
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
        """Получить список доступных моделей."""
        if not self.is_available:
            return []
        return ["CSLAV CNN (49 классов) - Евангелие 1606"]
    
    def _kinovar2black(self, img: np.ndarray) -> np.ndarray:
        """
        Преобразовать киноварь (красные символы) в черный цвет.
        
        Args:
            img: Входное изображение в формате BGR.
            
        Returns:
            Изображение с преобразованной киноварью.
        """
        h = img.shape[0]
        w = img.shape[1]
        img_flat = img.reshape(h * w, 3)
        img_flat = img_flat.T
        
        # Найти пиксели, где красный канал значительно превышает зеленый и синий
        a = np.logical_and(
            img_flat[2] / (img_flat[0] + 1) > 1.4,
            img_flat[2] / (img_flat[1] + 1) > 1.4
        )
        
        for idx in np.arange(len(a)):
            x = a.item(idx)
            if x:
                img_flat[0, idx] = 30
                img_flat[1, idx] = 30
                img_flat[2, idx] = 30
        
        img_flat = img_flat.T
        return img_flat.reshape(h, w, 3)
    
    def _prepare_img(self, filename: str) -> np.ndarray:
        """
        Предобработать изображение для OCR.
        
        Args:
            filename: Путь к файлу изображения.
            
        Returns:
            Бинаризованное изображение.
            
        Raises:
            FileNotFoundError: Если файл изображения не найден или не может быть прочитан.
        """
        import cv2
        
        img = cv2.imread(filename)
        
        # Проверка на успешную загрузку изображения
        if img is None or img.size == 0:
            raise FileNotFoundError(f"Не удалось загрузить изображение: {filename}. Файл может быть поврежден или иметь неподдерживаемый формат.")
        
        # Морфологическое расширение
        se = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        img_ex = cv2.morphologyEx(img, cv2.MORPH_DILATE, se)
        
        # Преобразовать киноварь в черный
        img_no_kinovar = self._kinovar2black(img_ex)
        
        # Конвертировать в оттенки серого
        img_gray = cv2.cvtColor(img_no_kinovar, cv2.COLOR_BGR2GRAY)
        
        # Бинаризация методом Оцу
        img_binary = cv2.threshold(
            img_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
        )[1]
        
        # Эрозия для разделения символов - используем ядро 1x1 чтобы сохранить иерархию контуров
        img_erode = cv2.erode(
            img_binary, np.ones((1, 1), np.uint8), iterations=1
        )
        
        return img_erode
    
    def _get_boxes(self, filename: str, min_h: int, max_h: int = 700, max_w: int = 400) -> List[List[int]]:
        """
        Найти контуры символов на изображении.
        
        Args:
            filename: Путь к файлу изображения.
            min_h: Минимальная высота контура.
            max_h: Максимальная высота контура.
            max_w: Максимальная ширина контура.
            
        Returns:
            Список ограничивающих прямоугольников [x, y, w, h].
        """
        import cv2
        
        img_prepared = self._prepare_img(filename)
        
        contours, hierarchy = cv2.findContours(
            img_prepared, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
        )
        
        boxes = []
        if hierarchy is not None:
            for idx, contour in enumerate(contours):
                (x, y, w, h) = cv2.boundingRect(contour)
                if hierarchy[0][idx][3] == 0 and min_h < h < max_h and w < max_w:
                    boxes.append([x, y, w, h])
        
        return boxes
    
    def _get_symbols(self, filename: str, min_h: int, max_h: int = 700, max_w: int = 400) -> List['Symbol']:
        """
        Распознать символы на изображении.
        
        Args:
            filename: Путь к файлу изображения.
            min_h: Минимальная высота контура.
            max_h: Максимальная высота контура.
            max_w: Максимальная ширина контура.
            
        Returns:
            Список объектов Symbol.
        """
        import cv2
        from tensorflow import keras
        
        if self.model is None:
            return []
        
        img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        boxes = self._get_boxes(filename, min_h, max_h, max_w)
        
        symbols = []
        for box in boxes:
            (x, y, w, h) = box
            symbol_pic = img[y:y + h, x:x + w]
            
            # Создать квадратное изображение
            size_max = max(w, h)
            out_pic = 255 * np.ones(shape=[size_max, size_max], dtype=np.uint8)
            
            if w > h:
                y_pos = size_max // 2 - h // 2
                out_pic[y_pos:y_pos + h, 0:w] = symbol_pic
            elif h > w:
                x_pos = size_max // 2 - w // 2
                out_pic[0:h, x_pos:x_pos + w] = symbol_pic
            else:
                out_pic = symbol_pic
            
            # Бинаризация и изменение размера до 56x56
            binary_out_pic = cv2.threshold(
                out_pic, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
            )[1]
            binary_out_pic = cv2.resize(binary_out_pic, (56, 56))
            
            # Создать объект символа
            new_symbol = Symbol(
                binary_out_pic, 
                (x, y, w, h), 
                self.model, 
                self.predictions_list
            )
            symbols.append(new_symbol)
        
        return symbols
    
    def _get_edges(self, boxes: List[List[int]], threshn: int) -> List[int]:
        """
        Найти границы строк по списку ограничивающих прямоугольников.
        
        Args:
            boxes: Список прямоугольников [x, y, w, h].
            threshn: Порог различия Y-координат для одной строки.
            
        Returns:
            Список Y-координат границ строк.
        """
        # Сортировать по Y-координате
        boxes_sorted = sorted(boxes, key=lambda box: box[1])
        
        new_list = []
        for el in boxes_sorted:
            new_list.append([1, el])
        
        rows = []
        for idx in range(len(new_list)):
            if new_list[idx][0] == 1:
                rows.append([])
                rows[-1].append(new_list[idx][1])
                new_list[idx][0] = 0
                
                for idx1 in range(idx + 1, len(new_list)):
                    if new_list[idx1][0] == 1 and abs(new_list[idx1][1][1] - new_list[idx][1][1]) < threshn:
                        rows[-1].append(new_list[idx1][1])
                        new_list[idx1][0] = 0
        
        edges = []
        for row in rows:
            x = float('inf')
            for box in row:
                if box[1] + box[3] < x:
                    x = box[1] + box[3]
            if x != float('inf'):
                edges.append(int(x))
        
        return edges
    
    def _symbols_to_rows(self, symbols_list: List['Symbol'], edges: List[int]) -> List[List['Symbol']]:
        """
        Распределить символы по строкам.
        
        Args:
            symbols_list: Список объектов Symbol.
            edges: Список границ строк.
            
        Returns:
            Список строк (списков символов), отсортированных сверху вниз.
        """
        # Сортировать по Y-координате (сверху вниз)
        symbols_sorted = sorted(symbols_list, key=lambda s: s.coordinates[1], reverse=True)
        
        rows = [[] for _ in range(len(edges))]
        
        i = 0
        for symbol in symbols_sorted:
            if i < len(edges) - 1:
                if symbol.coordinates[1] > edges[-i - 2]:
                    rows[i].append(symbol)
                else:
                    i += 1
            else:
                rows[i].append(symbol)
        
        # Перевернуть, чтобы строки были сверху вниз
        rows.reverse()
        
        # Сортировать символы в каждой строке слева направо
        for idx in range(len(rows)):
            rows[idx].sort(key=lambda s: s.coordinates[0])
        
        return rows
    
    def _get_raw_str(self, row: List['Symbol'], space: int) -> str:
        """
        Собрать текст из строки символов.
        
        Args:
            row: Список символов в строке.
            space: Размер пробела между словами.
            
        Returns:
            Строка текста.
        """
        raw_str = ''
        for idx in range(len(row)):
            if idx > 0 and row[idx].coordinates[0] - row[idx - 1].coordinates[2] > space:
                raw_str += ' '
            raw_str += row[idx].text
        return raw_str
    
    def _shit2utf8(self, text: str) -> str:
        """
        Декодировать текст из внутренней кодировки в UTF-8.
        
        Args:
            text: Текст во внутренней кодировке.
            
        Returns:
            Текст в UTF-8.
        """
        decoding_map = {
            i: i for i in 'ЙЦУКЕНГШЩЗХЪЭЖДЛОРПАВЫФЯЧСМИТЬБЮйцукенгшщзхъэждлорпавыфячсмитьбю.!";: -/\n\t'
        }
        
        decoding_map.update({
            '#': '\u0486',
            '$': '\u0486' + '\u0301',
            '%': '\u0486' + '\u0300',
            '&': '\u0483',
            '*': '\uA673',
            '+': '\u2DE1' + '\u0487',
            '0': '\u043E' + '\u0301',
            '1': '\u0301',
            '2': '\u0300',
            '3': '\u0486',
            '4': '\u0486' + '\u0301',
            '5': '\u0486' + '\u0300',
            '6': '\u0311',
            '7': '\u0483',
            '8': '\u033E',
            '9': '\u0436' + '\u0483',
            '<': '\u2DEF',
            '=': '\u2DE9' + '\u0487',
            '>': '\u2DEC' + '\u0487',
            '?': '\u2DF1' + '\u0487',
            '@': '\u0300',
            'A': '\u0430' + '\u0300',
            'B': '\u0463' + '\u0311',
            'C': '\u2DED' + '\u0487',
            'D': '\u0434' + '\u2DED' + '\u0487',
            'E': '\u0435' + '\u0300',
            'F': '\u0472',
            'G': '\u0433' + '\u0483',
            'H': '\u0461' + '\u0301',
            'I': '\u0406',
            'J': '\u0456' + '\u0300',
            'K': '\uA656' + '\u0486',
            'L': '\u043B' + '\u2DE3',
            'M': '\u0476',
            'N': '\u047A' + '\u0486',
            'O': '\u047A',
            'P': '\u0470',
            'Q': '\u047C',
            'R': '\u0440' + '\u0483',
            'S': '\u0467' + '\u0300',
            'T': '\u047E',
            'U': '\u041E' + '\u0443',
            'V': '\u0474',
            'W': '\u0460',
            'X': '\u046E',
            'Y': '\uA64B' + '\u0300',
            'Z': '\u0466',
            '\\': '\u0483',
            '^': '\u0311',
            '_': '\u033E',
            'a': '\u0430' + '\u0301',
            'b': '\u2DEA' + '\u0487',
            'c': '\u2DED' + '\u0487',
            'd': '\u2DE3',
            'e': '\u0435' + '\u0301',
            'f': '\u0473',
            'g': '\u2DE2' + '\u0487',
            'h': '\u044B' + '\u0301',
            'i': '\u0456',
            'j': '\u0456' + '\u0301',
            'k': '\uA657' + '\u0486',
            'l': '\u043B' + '\u0483',
            'm': '\u0477',
            'n': '\u047B' + '\u0486',
            'o': '\u047B',
            'p': '\u0471',
            'q': '\u047D',
            'r': '\u0440' + '\u2DED' + '\u0487',
            's': '\u0467' + '\u0301',
            't': '\u047F',
            'u': '\u1C82' + '\u0443',
            'v': '\u0475',
            'w': '\u0461',
            'x': '\u046F',
            'y': '\uA64B' + '\u0301',
            'z': '\u0467',
            '{': '\uA64B' + '\u0311',
            '|': '\u0467' + '\u0486' + '\u0300',
            '}': '\u0438' + '\u0483',
            '~': '\u0301',
            '.': '·',
            'Ђ': '\u0475' + '\u0301',
            'Ѓ': '\u0410' + '\u0486' + '\u0301',
            '‚': '\u201A',
            'ѓ': '\u0430' + '\u0486' + '\u0301',
            '„': '\u201E',
            '…': '\u046F' + '\u0483',
            '†': '\u0430' + '\u0311',
            '‡': '\u0456' + '\u0311',
            '€': '\u2DE5',
            '‰': '\u0467' + '\u0311',
            'Љ': '\u0466' + '\u0486',
            '‹': '\u0456' + '\u0483',
            'Њ': '\u0460' + '\u0486',
            'Ќ': '\u041E' + '\u0443' + '\u0486' + '\u0301',
            'Ћ': '\uA656' + '\u0486' + '\u0301',
            'Џ': '\u047A' + '\u0486' + '\u0301',
            'ђ': '\u0475' + '\u2DE2' + '\u0487',
            ''': '\u2018',
            ''': '\u2019',
            '"': '\u201C',
            '"': '\u201D',
            '•': '\u2DE4',
            '–': '\u2013',
            '—': '\u2014',
            '™': '\u0442' + '\u0483',
            'љ': '\u0467' + '\u0486',
            '›': '\u0475' + '\u0311',
            'њ': '\u0461' + '\u0486',
            'ќ': '\u1C82' + '\u0443' + '\u0486' + '\u0301',
            'ћ': '\uA657' + '\u0486' + '\u0301',
            'џ': '\u047B' + '\u0486' + '\u0301',
            'Ў': '\u041E' + '\u0443' + '\u0486',
            'ў': '\u1C82' + '\u0443' + '\u0486',
            'Ј': '\u0406' + '\u0486' + '\u0301',
            '¤': '\u0482',
            'Ґ': '\u0410' + '\u0486',
            '¦': '\u0445' + '\u0483',
            '§': '\u0447' + '\u0483',
            'Ё': '\u0463' + '\u0300',
            '©': '\u0441' + '\u0483',
            '«': '\u00AB',
            '¬': '\u00AC',
            '®': '\u0440' + '\u2DE3',
            'Ї': '\u0406' + '\u0486',
            '°': '\uA67E',
            '±': '\uA657' + '\u0486' + '\u0300',
            'І': '\u0406',
            'і': '\u0456' + '\u0308',
            'ґ': '\u0430' + '\u0486',
            'µ': '\u0443',
            'ё': '\u0463' + '\u0301',
            '№': '\u0430' + '\u0483',
            'є': '\u0454',
            '»': '\u00BB',
            'ј': '\u0456' + '\u0486' + '\u0301',
            'Ѕ': '\u0405',
            'ѕ': '\u0455',
            'ї': '\u0456' + '\u0486',
            'У': '\uA64A',
            'Э': '\u0462',
            'Я': '\uA656',
            'у': '\uA64B',
            'э': '\u0463',
            'я': '\uA657',
        })
        
        # Обработать специальные символы из Евангелия 1606
        special_chars = {
            'ӣ': '\u2DE0' + '\u0487',
            'Ӣ': '\u2DF6' + '\u0487',
            'μ': 'у',
            'Ө': '\u2DF0' + '\u0487',
            'Ҳ': '\u2DE6' + '\u0487',
            'Ҵ': '\u2DEE',
            'Ӥ': '\u2DF7',
            'ӥ': '\u2DE7' + '\u0487',
            'Ӯ': '\u2DF4',
            'Ҷ': 'ꙍ',
            'ӯ': '҇',
            'Ӫ': '\u2DF3',
            'ѹ': '\uFE2E' + '\uFE2F',
            'Ӂ': 'ꙋ',
            'Ұ': 'ᲂ',
            ',': ',',
            'ӡ': 'ꙁ',
            'ү': 'ᲁ',
            'ө': '\u2DF2',
            'Ҏ': '.',
            'ѣ': 'ᲇ',
            'Һ': 'ѽ',
            'Ѹ': '҃',
            'ұ': '\u2DE8',
            'Ѷ': '‶',
        }
        
        decoding_map.update(special_chars)
        
        # Декодировать текст
        utf8text = ''
        for sym in text:
            if sym in decoding_map:
                utf8text += decoding_map[sym]
            else:
                utf8text += sym
        
        return utf8text


class Symbol:
    """Класс для представления распознанного символа."""
    
    def __init__(self, matrix: np.ndarray, rectangle: Tuple[int, int, int, int], 
                 model, predictions_list: List[List[str]]):
        """
        Инициализировать символ.
        
        Args:
            matrix: Матрица изображения символа.
            rectangle: Ограничивающий прямоугольник (x, y, w, h).
            model: Загруженная CNN модель.
            predictions_list: Список соответствий предсказаний и символов.
        """
        import cv2
        from tensorflow import keras
        
        # Сохранить временный файл
        temp_path = 'temp_symbol.png'
        cv2.imwrite(temp_path, matrix)
        
        try:
            # Загрузить и подготовить изображение
            image = keras.preprocessing.image.load_img(temp_path, target_size=(56, 56, 3))
            input_arr = keras.preprocessing.image.img_to_array(image)
            num_arr = np.array([input_arr])
            
            # Получить предсказание модели
            result = model.predict([num_arr], verbose=0)
            
            # Найти соответствующий символ
            self.text = ''
            for prediction in predictions_list:
                if len(prediction) == 2 and prediction[1] == str(result):
                    self.text = prediction[0]
                    break
        finally:
            # Удалить временный файл
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # Сохранить координаты
        self.coordinates = (
            rectangle[0], 
            rectangle[1], 
            rectangle[0] + rectangle[2], 
            rectangle[1] + rectangle[3]
        )
