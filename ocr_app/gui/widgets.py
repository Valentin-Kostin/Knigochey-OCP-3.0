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
    QSlider,
)
from PySide6.QtGui import QPixmap, QImage, QFont, QTransform
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
        self._rotation_angle = 0  # Угол поворота в градусах
        
        # Элементы управления поворотом
        rotate_layout = QHBoxLayout()
        
        self._rotate_left_btn = QPushButton("⟲ 90°")
        self._rotate_left_btn.setMaximumWidth(60)
        self._rotate_left_btn.setEnabled(False)
        self._rotate_left_btn.clicked.connect(self._rotate_left)
        
        self._rotate_right_btn = QPushButton("90° ⟳")
        self._rotate_right_btn.setMaximumWidth(60)
        self._rotate_right_btn.setEnabled(False)
        self._rotate_right_btn.clicked.connect(self._rotate_right)
        
        self._rotate_180_btn = QPushButton("180°")
        self._rotate_180_btn.setMaximumWidth(60)
        self._rotate_180_btn.setEnabled(False)
        self._rotate_180_btn.clicked.connect(self._rotate_180)
        
        self._rotate_slider = QSlider(Qt.Orientation.Horizontal)
        self._rotate_slider.setMinimum(-180)
        self._rotate_slider.setMaximum(180)
        self._rotate_slider.setValue(0)
        self._rotate_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._rotate_slider.setTickInterval(90)
        self._rotate_slider.valueChanged.connect(self._on_rotate_slider_changed)
        self._rotate_slider.setEnabled(False)
        
        self._rotate_label = QLabel("0°")
        self._rotate_label.setMinimumWidth(40)
        self._rotate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        rotate_layout.addStretch()
        rotate_layout.addWidget(self._rotate_left_btn)
        rotate_layout.addWidget(self._rotate_180_btn)
        rotate_layout.addWidget(self._rotate_right_btn)
        rotate_layout.addWidget(self._rotate_slider)
        rotate_layout.addWidget(self._rotate_label)
        rotate_layout.addStretch()
        
        layout.addLayout(rotate_layout)
    
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
        self._rotation_angle = 0
        self._update_display()
        
        self._zoom_in_btn.setEnabled(True)
        self._zoom_out_btn.setEnabled(True)
        self._rotate_left_btn.setEnabled(True)
        self._rotate_right_btn.setEnabled(True)
        self._rotate_180_btn.setEnabled(True)
        self._rotate_slider.setEnabled(True)
        
        self.image_loaded.emit(str(image_path))
        return True
    
    def clear(self) -> None:
        """Очистить текущее изображение."""
        self._current_image_path = None
        self._pixmap = None
        self._original_pixmap = None
        self._zoom_factor = 1.0
        self._rotation_angle = 0
        
        self._label.clear()
        self._label.setText("Изображение не загружено")
        self._label.setStyleSheet("QLabel { color: gray; }")
        self._zoom_label.setText("100%")
        self._rotate_label.setText("0°")
        self._rotate_slider.setValue(0)
        self._zoom_in_btn.setEnabled(False)
        self._zoom_out_btn.setEnabled(False)
        self._rotate_left_btn.setEnabled(False)
        self._rotate_right_btn.setEnabled(False)
        self._rotate_180_btn.setEnabled(False)
        self._rotate_slider.setEnabled(False)
    
    def _update_display(self) -> None:
        """Обновить отображаемый pixmap на основе коэффициента масштабирования и поворота."""
        if self._original_pixmap is None:
            return
        
        # Сначала применяем поворот к оригинальному изображению
        if self._rotation_angle != 0:
            transform = QTransform()
            transform.rotate(self._rotation_angle)
            rotated_pixmap = self._original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        else:
            rotated_pixmap = self._original_pixmap
        
        # Затем применяем масштабирование
        if self._zoom_factor == 1.0:
            self._pixmap = rotated_pixmap
        else:
            new_size = rotated_pixmap.size() * self._zoom_factor
            self._pixmap = rotated_pixmap.scaled(
                new_size,
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
    
    def _rotate_left(self) -> None:
        """Повернуть изображение на 90 градусов влево."""
        self._rotation_angle = (self._rotation_angle - 90) % 360
        self._rotate_slider.setValue(self._rotation_angle)
        self._update_display()
    
    def _rotate_right(self) -> None:
        """Повернуть изображение на 90 градусов вправо."""
        self._rotation_angle = (self._rotation_angle + 90) % 360
        self._rotate_slider.setValue(self._rotation_angle)
        self._update_display()
    
    def _rotate_180(self) -> None:
        """Повернуть изображение на 180 градусов."""
        self._rotation_angle = (self._rotation_angle + 180) % 360
        self._rotate_slider.setValue(self._rotation_angle)
        self._update_display()
    
    def _on_rotate_slider_changed(self, value: int) -> None:
        """Обработать изменение ползунка поворота."""
        self._rotation_angle = value
        self._rotate_label.setText(f"{value}°")
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
        
        # Установить моноширинный шрифт по умолчанию для лучшей читаемости
        self._default_font = QFont("Courier New", 11)
        self._default_font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(self._default_font)
        
        # Включить перенос строк
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # Установить текст-заполнитель
        self.setPlaceholderText("Здесь появится результат OCR...\n\nВы можете отредактировать этот текст перед экспортом.")
        
        # Подключить сигнал
        self.textChanged.connect(self.text_changed.emit)
        
        # Создать основной макет с панелью инструментов
        self._setup_font_toolbar()
    
    def _setup_font_toolbar(self) -> None:
        """Настроить панель инструментов для работы со шрифтами."""
        # Основной вертикальный макет
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Панель инструментов шрифтов
        font_toolbar = QWidget()
        font_layout = QHBoxLayout(font_toolbar)
        font_layout.setContentsMargins(0, 0, 0, 5)
        font_layout.setSpacing(5)
        
        # Выбор шрифта
        font_layout.addWidget(QLabel("Шрифт:"))
        self._font_combo = QComboBox()
        self._font_combo.setEditable(True)
        self._font_combo.setMinimumWidth(150)
        # Популярные шрифты
        common_fonts = [
            "Courier New", "Consolas", "Lucida Console", "Monaco",  # Моноширинные
            "Arial", "Helvetica", "Verdana", "Tahoma",  # Без засечек
            "Times New Roman", "Georgia", "Palatino", "Garamond"  # С засечками
        ]
        for font_name in common_fonts:
            self._font_combo.addItem(font_name)
        self._font_combo.setCurrentText("Courier New")
        self._font_combo.currentTextChanged.connect(self._on_font_changed)
        font_layout.addWidget(self._font_combo)
        
        # Размер шрифта
        font_layout.addWidget(QLabel("Размер:"))
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setMinimum(6)
        self._font_size_spin.setMaximum(72)
        self._font_size_spin.setValue(11)
        self._font_size_spin.setFixedWidth(60)
        self._font_size_spin.valueChanged.connect(self._on_font_size_changed)
        font_layout.addWidget(self._font_size_spin)
        
        # Кнопки форматирования
        self._bold_btn = QPushButton("B")
        self._bold_btn.setToolTip("Жирный")
        self._bold_btn.setCheckable(True)
        self._bold_btn.setFont(QFont(self._default_font.family(), self._default_font.pointSize(), QFont.Weight.Bold))
        self._bold_btn.clicked.connect(self._on_bold_clicked)
        font_layout.addWidget(self._bold_btn)
        
        self._italic_btn = QPushButton("I")
        self._italic_btn.setToolTip("Курсив")
        self._italic_btn.setCheckable(True)
        self._italic_btn.setFont(QFont(self._default_font.family(), self._default_font.pointSize(), QFont.Weight.Normal, True))
        self._italic_btn.clicked.connect(self._on_italic_clicked)
        font_layout.addWidget(self._italic_btn)
        
        self._underline_btn = QPushButton("U")
        self._underline_btn.setToolTip("Подчёркнутый")
        self._underline_btn.setCheckable(True)
        underline_font = QFont(self._default_font.family(), self._default_font.pointSize())
        underline_font.setUnderline(True)
        self._underline_btn.setFont(underline_font)
        self._underline_btn.clicked.connect(self._on_underline_clicked)
        font_layout.addWidget(self._underline_btn)
        
        font_layout.addStretch()
        
        # Добавить панель инструментов и текстовый редактор в основной макет
        main_layout.addWidget(font_toolbar)
        main_layout.addWidget(self)
        
        # Установить макет виджету
        self.setLayout(main_layout)
    
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
    
    def _on_font_changed(self, font_name: str) -> None:
        """Обработать изменение шрифта."""
        current_format = self.currentCharFormat()
        new_font = current_format.font()
        new_font.setFamily(font_name)
        current_format.setFont(new_font)
        self.setCurrentCharFormat(current_format)
        # Также обновляем шрифт для нового текста
        self.setFont(new_font)
    
    def _on_font_size_changed(self, size: int) -> None:
        """Обработать изменение размера шрифта."""
        current_format = self.currentCharFormat()
        new_font = current_format.font()
        new_font.setPointSize(size)
        current_format.setFont(new_font)
        self.setCurrentCharFormat(current_format)
        # Также обновляем размер шрифта для нового текста
        self.setFont(new_font)
    
    def _on_bold_clicked(self, checked: bool) -> None:
        """Обработать нажатие кнопки жирного шрифта."""
        fmt = self.currentCharFormat()
        font = fmt.font()
        font.setBold(checked)
        fmt.setFont(font)
        self.setCurrentCharFormat(fmt)
        self._bold_btn.setChecked(checked)
    
    def _on_italic_clicked(self, checked: bool) -> None:
        """Обработать нажатие кнопки курсива."""
        fmt = self.currentCharFormat()
        font = fmt.font()
        font.setItalic(checked)
        fmt.setFont(font)
        self.setCurrentCharFormat(fmt)
        self._italic_btn.setChecked(checked)
    
    def _on_underline_clicked(self, checked: bool) -> None:
        """Обработать нажатие кнопки подчёркивания."""
        fmt = self.currentCharFormat()
        font = fmt.font()
        font.setUnderline(checked)
        fmt.setFont(font)
        self.setCurrentCharFormat(fmt)
        self._underline_btn.setChecked(checked)


class EngineSelectorWidget(QGroupBox):
    """Виджет для выбора OCR-движка и модели."""
    
    engine_changed = Signal(str)  # Испускает имя движка
    model_changed = Signal(str)   # Испускает имя модели
    device_changed = Signal(str)  # Испускает выбранное устройство (cpu/cuda)
    
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
        
        # Выбор устройства (CPU/GPU)
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Устройство:"))
        
        self._device_combo = QComboBox()
        self._device_combo.addItem("Авто (CUDA если доступно)", "auto")
        self._device_combo.addItem("CPU (Процессор)", "cpu")
        self._device_combo.addItem("GPU (CUDA)", "cuda")
        self._device_combo.setMinimumWidth(200)
        self._device_combo.currentTextChanged.connect(self._on_device_changed)
        device_layout.addWidget(self._device_combo)
        device_layout.addStretch()
        
        layout.addLayout(device_layout)
        
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
    
    def get_selected_device(self) -> str:
        """Получить выбранное устройство (cpu/cuda/auto)."""
        return self._device_combo.currentData()
    
    def _on_engine_changed(self, engine_name: str) -> None:
        """Обработать изменение выбора движка."""
        # Удалить галочку из отображения
        clean_name = engine_name.split(" ", 1)[-1] if " " in engine_name else engine_name
        self.engine_changed.emit(clean_name)
    
    def _on_model_changed(self, model_name: str) -> None:
        """Обработать изменение выбора модели."""
        if model_name != "Нет доступных моделей":
            self.model_changed.emit(model_name)
    
    def _on_device_changed(self, device_name: str) -> None:
        """Обработать изменение выбора устройства."""
        device_data = self._device_combo.currentData()
        self.device_changed.emit(device_data)


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
        
        self._orientation_check = QCheckBox("Определение ориентации (OSD)")
        self._orientation_check.setChecked(True)
        self._orientation_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._orientation_check)
        
        self._deskew_check = QCheckBox("Исправление перекоса")
        self._deskew_check.setChecked(True)
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
            "orientation": self._orientation_check.isChecked(),
            "deskew": self._deskew_check.isChecked(),
            "contrast": self._contrast_check.isChecked(),
            "binarization": self._binarize_check.isChecked(),
        }
    
    def set_from_config(self, config: dict) -> None:
        """Установить опции из словаря конфигурации."""
        self._denoise_check.setChecked(config.get("denoise", False))
        self._clahe_check.setChecked(config.get("clahe", True))
        self._orientation_check.setChecked(config.get("orientation", True))
        self._deskew_check.setChecked(config.get("deskew", False))
        self._contrast_check.setChecked(config.get("contrast", True))
        self._binarize_check.setChecked(config.get("binarization", False))
    
    def _on_preset_changed(self, index: int) -> None:
        """Обработать изменение выбора пресета."""
        preset = self._preset_combo.currentData()
        
        if preset == "default":
            self.set_from_config({
                "denoise": False, "clahe": True, "orientation": True, "deskew": True,
                "contrast": True, "binarization": False
            })
        elif preset == "old_printed":
            self.set_from_config({
                "denoise": True, "clahe": True, "orientation": True, "deskew": True,
                "contrast": True, "binarization": False
            })
        elif preset == "handwritten":
            self.set_from_config({
                "denoise": True, "clahe": True, "orientation": True, "deskew": True,
                "contrast": True, "binarization": False
            })
        elif preset == "low_quality":
            self.set_from_config({
                "denoise": True, "clahe": True, "orientation": True, "deskew": True,
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
