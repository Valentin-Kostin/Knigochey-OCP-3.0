# Интеграция CSLAV OCR

## Обзор

В проект `ocr_app` успешно интегрирован движок **CSLAV OCR** для распознавания старославянских текстов. Этот движок использует собственную CNN-модель, обученную на Евангелии 1606 года, и поддерживает 49 классов символов со специальным декодером кодировок.

## Что было сделано

### 1. Создан файл `ocr_app/engine/cslav_engine.py`

Этот файл содержит:
- **CSLAVEngine** - класс OCR-движка, наследующий базовый класс `OCREngine`
- **Symbol** - вспомогательный класс для представления распознанных символов

#### Ключевые возможности CSLAVEngine:

1. **Предобработка изображений**:
   - Преобразование киновари (красных символов) в черный цвет
   - Морфологическое расширение
   - Бинаризация методом Оцу
   - Эрозия для разделения символов

2. **Распознавание символов**:
   - Поиск контуров символов
   - Нормализация размера до 56x56 пикселей
   - Предсказание с помощью CNN модели (49 классов)

3. **Постобработка**:
   - Группировка символов в строки
   - Сборка текста из строк
   - Декодирование специальной кодировки в UTF-8

4. **Декодер кодировок**:
   - Поддержка стандартных славянских символов
   - Специальные символы Евангелия 1606 года
   - Комбинируемые диакритические знаки

### 2. Обновлен `ocr_app/engine/__init__.py`

Добавлен экспорт нового движка:
```python
from .cslav_engine import CSLAVEngine

__all__ = [
    "OCREngine",
    "OCRResult",
    "TesseractEngine",
    "KrakenEngine",
    "TrOCREngine",
    "CSLAVEngine",  # Новый движок
]
```

## Установка зависимостей

Для работы CSLAV OCR требуются следующие пакеты:

```bash
pip install tensorflow opencv-python numpy pillow
```

### Минимальные версии:
- TensorFlow >= 2.0
- OpenCV >= 4.0
- NumPy >= 1.19
- Pillow >= 8.0

## Использование

### Базовое использование

```python
from pathlib import Path
from ocr_app.engine import CSLAVEngine

# Создать движок (использует модель по умолчанию)
engine = CSLAVEngine()

# Проверить доступность
if engine.is_ready():
    # Распознать текст
    result = engine.recognize(Path("path/to/image.png"))
    print(result.text)
    print(f"Уверенность: {result.confidence}")
    print(f"Время обработки: {result.processing_time_ms}мс")
else:
    print("CSLAV OCR недоступен - проверьте установку зависимостей")
```

### С указанием пути к модели

```python
from pathlib import Path
from ocr_app.engine import CSLAVEngine

model_path = Path("/path/to/machine.h5")
engine = CSLAVEngine(model_path=model_path)

if engine.is_ready():
    result = engine.recognize(Path("image.png"))
    print(result.get_formatted_text())
```

### В составе приложения

```python
from ocr_app.engine import (
    TesseractEngine, 
    KrakenEngine, 
    TrOCREngine,
    CSLAVEngine  # Новый движок
)

# Создать все доступные движки
engines = [
    TesseractEngine(),
    KrakenEngine(),
    TrOCREngine(),
    CSLAVEngine(),
]

# Найти доступные
available = [e for e in engines if e.is_ready()]
print(f"Доступно движков: {len(available)}")

for engine in available:
    print(f"- {engine.name}: {engine.get_available_models()}")
```

## Структура файлов

```
/workspace/
├── ocr_app/
│   └── engine/
│       ├── __init__.py              # Обновлён
│       ├── base.py                  # Без изменений
│       ├── cslav_engine.py          # НОВЫЙ ФАЙЛ
│       ├── tesseract_engine.py      # Без изменений
│       ├── kraken_engine.py         # Без изменений
│       └── trocr_engine.py          # Без изменений
└── CSLAV_OCR_1.0-main/
    ├── machine.h5                   # Модель CNN
    └── CSLAV_OCR-main/
        └── predictions.txt          # Соответствия символов
```

## Особенности CSLAV OCR

### Преимущества

1. **Специализация**: Обучен специально на старославянских текстах
2. **Исторические символы**: Поддерживает 49 классов, включая:
   - Юсы (юс малый, юс большой)
   - Ять с различными модификациями
   - Ижица, тета, омега
   - Комбинируемые диакритические знаки (титла, каморы и др.)

3. **Декодер кодировок**: Преобразует внутреннюю кодировку в правильный Unicode

4. **Обработка киновари**: Автоматически распознаёт красные символы

### Ограничения

1. **Требует TensorFlow**: В отличие от Tesseract/Kraken, нужен TensorFlow
2. **49 классов**: Ограниченный набор символов по сравнению с современными OCR
3. **Размер входа**: Все символы масштабируются до 56x56 пикселей
4. **Нет уверенности**: Не предоставляет оценку уверенности распознавания

## Тестирование

Проверить работу движка можно командой:

```bash
cd /workspace
python -c "
from ocr_app.engine import CSLAVEngine
engine = CSLAVEngine()
print(f'Статус: {\"доступен\" if engine.is_ready() else \"недоступен\"}')
print(f'Модели: {engine.get_available_models()}')
"
```

## Интеграция с GUI

Для добавления CSLAV в графический интерфейс:

1. Движок автоматически появится в списке доступных после установки TensorFlow
2. Пользователь сможет выбрать его как любой другой OCR-движок
3. Результаты будут отображаться в том же формате, что и другие движки

## Будущие улучшения

Возможные направления развития:

1. **Дообучение модели**: Использовать датасеты из `CSLAV_OCR_1.0-main/cnn/`
2. **Поддержка PDF**: Интегрировать с `main_with_pdf.py`
3. **NK Decoder**: Добавить поддержку `nk_decoder.py` для улучшенного декодирования
4. **Batch processing**: Пакетная обработка нескольких изображений
5. **GUI настройки**: Параметры предобработки через интерфейс

## Ресурсы

- Оригинальный проект: `CSLAV_OCR_1.0-main/`
- Модель: `machine.h5` (1.6 MB, 49 классов)
- Датасет для обучения: `cnn/train/`, `cnn/val/`, `cnn/test/`
- Примеры использования: `CSLAV_OCR-main/main.py`
