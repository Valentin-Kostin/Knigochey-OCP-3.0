"""
Пользовательские виджеты для графического интерфейса OCR-приложения.
"""

from pathlib import Path
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QTextEdit,
    QComboBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QProgressBar,
    QFrame,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtGui import QPixmap, QImage, QFont
from PySide6.QtCore import Qt, Signal


class ImagePreviewWidget(QFrame):
    """Виджет для предпросмотра изображения с масштабированием и перемещением."""
    
    image_loaded = Signal(str)  # Испускает путь к файлу при загрузке изображения
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Инициализировать виджет предпросмотра изображения."""
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self._current_image_path: Optional[Path] = None
        self._pixmap: Optional[QPixmap] = None
        
        # Настроить UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(200, 150)
        self._label.setText("Изображение не загружено")
        self._label.setStyleSheet("QLabel { color: gray; }")
        
        layout.addWidget(self._label)
        
        # Элементы управления масштабированием
        zoom_layout = QHBoxLayout()
        
        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setMaximumWidth(40)
        self._zoom_in_btn.setEnabled(False)
        self._zoom_in_btn.clicked.connect(self._zoom_in)
        
        self._zoom_out_btn = QPushButton("-")
        self._zoom_out_btn.setMaximumWidth(40)
        self._zoom_out_btn.setEnabled(False)
        self._zoom_out_btn.clicked.connect(self._zoom_out)
        
        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(60)
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        zoom_layout.addStretch()
        zoom_layout.addWidget(self._zoom_out_btn)
        zoom_layout.addWidget(self._zoom_label)
        zoom_layout.addWidget(self._zoom_in_btn)
        zoom_layout.addStretch()
        
        layout.addLayout(zoom_layout)
        
        self._zoom_factor = 1.0
        self._original_pixmap: Optional[QPixmap] = None
    
    def load_image(self, image_path: Path) -> bool:
        """
        Загрузить изображение для предпросмотра.
        
        Args:
            image_path: Путь к файлу изображения.
            
        Returns:
            True если успешно, False иначе.
        """
        if not image_path.exists():
            return False
        
        self._current_image_path = image_path
        self._original_pixmap = QPixmap(str(image_path))
        
        if self._original_pixmap.isNull():
            self._label.setText("Не удалось загрузить изображение")
            return False
        
        self._zoom_factor = 1.0
        self._update_display()
        
        self._zoom_in_btn.setEnabled(True)
        self._zoom_out_btn.setEnabled(True)
        
        self.image_loaded.emit(str(image_path))
        return True
    
    def clear(self) -> None:
        """Очистить текущее изображение."""
        self._current_image_path = None
        self._pixmap = None
        self._original_pixmap = None
        self._zoom_factor = 1.0
        
        self._label.clear()
        self._label.setText("Изображение не загружено")
        self._label.setStyleSheet("QLabel { color: gray; }")
        self._zoom_label.setText("100%")
        self._zoom_in_btn.setEnabled(False)
        self._zoom_out_btn.setEnabled(False)
    
    def _update_display(self) -> None:
        """Обновить отображаемый pixmap на основе коэффициента масштабирования."""
        if self._original_pixmap is None:
            return
        
        if self._zoom_factor == 1.0:
            self._pixmap = self._original_pixmap
        else:
            new_size = self._original_pixmap.size() * self._zoom_factor
            self._pixmap = self._original_pixmap.scaled(
                new_size.toSize(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        
        self._label.setPixmap(self._pixmap)
        self._label.setStyleSheet("")
        self._zoom_label.setText(f"{int(self._zoom_factor * 100)}%")
    
    def _zoom_in(self) -> None:
        """Увеличить масштаб изображения."""
        if self._zoom_factor < 5.0:
            self._zoom_factor *= 1.25
            self._update_display()
    
    def _zoom_out(self) -> None:
        """Уменьшить масштаб изображения."""
        if self._zoom_factor > 0.2:
            self._zoom_factor /= 1.25
            self._update_display()
    
    def get_current_image_path(self) -> Optional[Path]:
        """Получить путь к текущему изображению."""
        return self._current_image_path


class TextEditorWidget(QTextEdit):
    """Виджет текстового редактора для отображения и редактирования результатов OCR."""
    
    text_changed = Signal()  # Испускается при изменении текста
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Инициализировать виджет текстового редактора."""
        super().__init__(parent)
        
        # Установить моноширинный шрифт для лучшей читаемости
        font = QFont("Courier New", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Включить перенос строк
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # Установить текст-заполнитель
        self.setPlaceholderText("Здесь появится результат OCR...\n\nВы можете отредактировать этот текст перед экспортом.")
        
        # Подключить сигнал
        self.textChanged.connect(self.text_changed.emit)
    
    def set_result_text(self, text: str, metadata: Optional[str] = None) -> None:
        """
        Установить текст результата OCR с опциональными метаданными.
        
        Args:
            text: Распознанный текст.
            metadata: Опциональный заголовок метаданных.
        """
        if metadata:
            self.setPlainText(f"{metadata}\n\n{text}")
        else:
            self.setPlainText(text)
    
    def clear(self) -> None:
        """Очистить текстовый редактор."""
        self.clear()
        self.setPlaceholderText("Здесь появится результат OCR...\n\nВы можете отредактировать этот текст перед экспортом.")
    
    def get_text(self) -> str:
        """Получить текущее содержимое текста."""
        return self.toPlainText()


class EngineSelectorWidget(QGroupBox):
    """Виджет для выбора OCR-движка и модели."""
    
    engine_changed = Signal(str)  # Испускает имя движка
    model_changed = Signal(str)   # Испускает имя модели
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Инициализировать виджет выбора движка."""
        super().__init__("OCR-движок", parent)
        
        layout = QVBoxLayout(self)
        
        # Выбор движка
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("Движок:"))
        
        self._engine_combo = QComboBox()
        self._engine_combo.setMinimumWidth(200)
        self._engine_combo.currentTextChanged.connect(self._on_engine_changed)
        engine_layout.addWidget(self._engine_combo)
        engine_layout.addStretch()
        
        layout.addLayout(engine_layout)
        
        # Выбор модели
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель:"))
        
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(200)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        model_layout.addWidget(self._model_combo)
        model_layout.addStretch()
        
        layout.addLayout(model_layout)
        
        # Статус движка
        self._status_label = QLabel("Статус: Не инициализирован")
        self._status_label.setStyleSheet("color: orange;")
        layout.addWidget(self._status_label)
        
        layout.addStretch()
    
    def populate_engines(self, engines: list[tuple[str, bool]]) -> None:
        """
        Заполнить комбо-бокс движков.
        
        Args:
            engines: Список кортежей (имя_движка, доступен).
        """
        self._engine_combo.clear()
        
        for name, available in engines:
            status = "✓" if available else "✗"
            self._engine_combo.addItem(f"{status} {name}", userData=name)
        
        if self._engine_combo.count() > 0:
            self._engine_combo.setCurrentIndex(0)
    
    def populate_models(self, models: list[str]) -> None:
        """
        Заполнить комбо-бокс моделей.
        
        Args:
            models: Список названий моделей.
        """
        self._model_combo.clear()
        
        if not models:
            self._model_combo.addItem("Нет доступных моделей")
            self._model_combo.setEnabled(False)
        else:
            for model in models:
                self._model_combo.addItem(model)
            self._model_combo.setEnabled(True)
    
    def set_status(self, status: str, success: bool = True) -> None:
        """
        Установить сообщение статуса движка.
        
        Args:
            status: Сообщение статуса.
            success: Указывает ли статус на успех.
        """
        self._status_label.setText(f"Статус: {status}")
        
        if success:
            self._status_label.setStyleSheet("color: green;")
        elif status == "Не инициализирован":
            self._status_label.setStyleSheet("color: orange;")
        else:
            self._status_label.setStyleSheet("color: red;")
    
    def get_selected_engine(self) -> Optional[str]:
        """Получить имя выбранного в данный момент движка."""
        return self._engine_combo.currentData()
    
    def get_selected_model(self) -> Optional[str]:
        """Получить имя выбранной в данный момент модели."""
        if not self._model_combo.isEnabled():
            return None
        return self._model_combo.currentText()
    
    def _on_engine_changed(self, engine_name: str) -> None:
        """Обработать изменение выбора движка."""
        # Удалить галочку из отображения
        clean_name = engine_name.split(" ", 1)[-1] if " " in engine_name else engine_name
        self.engine_changed.emit(clean_name)
    
    def _on_model_changed(self, model_name: str) -> None:
        """Обработать изменение выбора модели."""
        if model_name != "Нет доступных моделей":
            self.model_changed.emit(model_name)


class PreprocessingOptionsWidget(QGroupBox):
    """Виджет для настройки параметров предобработки."""
    
    options_changed = Signal()  # Испускается при изменении любой опции
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Инициализировать виджет параметров предобработки."""
        super().__init__("Предобработка", parent)
        
        layout = QVBoxLayout(self)
        
        # Выбор пресета
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Пресет:"))
        
        self._preset_combo = QComboBox()
        self._preset_combo.addItem("По умолчанию", "default")
        self._preset_combo.addItem("Старый печатный текст", "old_printed")
        self._preset_combo.addItem("Рукописный", "handwritten")
        self._preset_combo.addItem("Скан низкого качества", "low_quality")
        self._preset_combo.addItem("Пользовательский", "custom")
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self._preset_combo)
        preset_layout.addStretch()
        
        layout.addLayout(preset_layout)
        
        # Индивидуальные опции
        self._denoise_check = QCheckBox("Шумоподавление")
        self._denoise_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._denoise_check)
        
        self._clahe_check = QCheckBox("Улучшение контраста (CLAHE)")
        self._clahe_check.setChecked(True)
        self._clahe_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._clahe_check)
        
        self._deskew_check = QCheckBox("Исправление перекоса")
        self._deskew_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._deskew_check)
        
        self._contrast_check = QCheckBox("Коррекция контраста")
        self._contrast_check.setChecked(True)
        self._contrast_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._contrast_check)
        
        self._binarize_check = QCheckBox("Бинаризация")
        self._binarize_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._binarize_check)
        
        layout.addStretch()
    
    def get_config(self) -> dict:
        """Получить текущую конфигурацию предобработки."""
        return {
            "denoise": self._denoise_check.isChecked(),
            "clahe": self._clahe_check.isChecked(),
            "deskew": self._deskew_check.isChecked(),
            "contrast": self._contrast_check.isChecked(),
            "binarization": self._binarize_check.isChecked(),
        }
    
    def set_from_config(self, config: dict) -> None:
        """Установить опции из словаря конфигурации."""
        self._denoise_check.setChecked(config.get("denoise", False))
        self._clahe_check.setChecked(config.get("clahe", True))
        self._deskew_check.setChecked(config.get("deskew", False))
        self._contrast_check.setChecked(config.get("contrast", True))
        self._binarize_check.setChecked(config.get("binarization", False))
    
    def _on_preset_changed(self, index: int) -> None:
        """Обработать изменение выбора пресета."""
        preset = self._preset_combo.currentData()
        
        if preset == "default":
            self.set_from_config({
                "denoise": False, "clahe": True, "deskew": False,
                "contrast": True, "binarization": False
            })
        elif preset == "old_printed":
            self.set_from_config({
                "denoise": True, "clahe": True, "deskew": True,
                "contrast": True, "binarization": False
            })
        elif preset == "handwritten":
            self.set_from_config({
                "denoise": True, "clahe": True, "deskew": True,
                "contrast": True, "binarization": False
            })
        elif preset == "low_quality":
            self.set_from_config({
                "denoise": True, "clahe": True, "deskew": True,
                "contrast": True, "binarization": True
            })
        # Custom сохраняет текущие настройки
        
        self.options_changed.emit()
    
    def _on_option_changed(self) -> None:
        """Обработать изменение индивидуальной опции."""
        self._preset_combo.setCurrentText("Пользовательский")
        self.options_changed.emit()


class StatusBarWidget(QWidget):
    """Виджет строки состояния, отображающий прогресс и сообщения."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Инициализировать виджет строки состояния."""
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Метка статуса
        self._status_label = QLabel("Готов")
        self._status_label.setMinimumWidth(200)
        layout.addWidget(self._status_label)
        
        # Индикатор прогресса
        self._progress = QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setMaximumWidth(200)
        self._progress.hide()
        layout.addWidget(self._progress)
        
        # Информационная метка
        self._info_label = QLabel("")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._info_label)
    
    def set_message(self, message: str) -> None:
        """Установить сообщение статуса."""
        self._status_label.setText(message)
    
    def set_progress(self, value: int, show: bool = True) -> None:
        """
        Установить значение прогресса.
        
        Args:
            value: Значение прогресса (0-100).
            show: Показывать ли индикатор прогресса.
        """
        self._progress.setValue(value)
        if show:
            self._progress.show()
        else:
            self._progress.hide()
    
    def set_info(self, info: str) -> None:
        """Установить информационный текст."""
        self._info_label.setText(info)
    
    def reset(self) -> None:
        """Сбросить строку состояния к состоянию по умолчанию."""
        self._status_label.setText("Готов")
        self._progress.setValue(0)
        self._progress.hide()
        self._info_label.setText("")
