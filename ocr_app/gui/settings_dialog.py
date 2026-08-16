"""
Диалог настроек приложения.
Позволяет пользователю настроить путь к Tesseract и другие параметры.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QCheckBox,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    """Диалог настроек приложения."""
    
    def __init__(self, config_manager, parent=None):
        """
        Инициализировать диалог настроек.
        
        Args:
            config_manager: Экземпляр ConfigManager для чтения/записи настроек.
            parent: Родительское окно.
        """
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(500)
        self.setModal(True)
        
        self.config = config_manager
        
        layout = QVBoxLayout(self)
        
        # Секция: Путь к Tesseract
        tesseract_group = QGroupBox("Путь к Tesseract OCR")
        tesseract_layout = QVBoxLayout(tesseract_group)
        
        tesseract_info = QLabel(
            "Укажите полный путь к исполняемому файлу tesseract.exe.\n"
            "Оставьте пустым, если Tesseract установлен в системном PATH."
        )
        tesseract_info.setWordWrap(True)
        tesseract_layout.addWidget(tesseract_info)
        
        tesseract_path_layout = QHBoxLayout()
        self._tesseract_path_edit = QLineEdit()
        self._tesseract_path_edit.setPlaceholderText("Например: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
        self._tesseract_path_edit.setText(self.config.get_tesseract_path())
        tesseract_path_layout.addWidget(self._tesseract_path_edit)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self._browse_tesseract)
        tesseract_path_layout.addWidget(browse_btn)
        
        tesseract_layout.addLayout(tesseract_path_layout)
        layout.addWidget(tesseract_group)
        
        # Секция: Параметры предобработки
        preprocessing_group = QGroupBox("Предобработка изображений")
        preprocessing_layout = QVBoxLayout(preprocessing_group)
        
        self._osd_checkbox = QCheckBox("Автоматическое определение ориентации (OSD)")
        self._osd_checkbox.setChecked(self.config.get_osd_enabled())
        self._osd_checkbox.setToolTip(
            "Использует Tesseract OSD для определения правильного поворота страницы (0°, 90°, 180°, 270°)"
        )
        preprocessing_layout.addWidget(self._osd_checkbox)
        
        self._deskew_checkbox = QCheckBox("Исправление перекоса (Deskew)")
        self._deskew_checkbox.setChecked(self.config.get_deskew_enabled())
        self._deskew_checkbox.setToolTip(
            "Автоматически выравнивает текст при небольшом наклоне (до ±5°)"
        )
        preprocessing_layout.addWidget(self._deskew_checkbox)
        
        layout.addWidget(preprocessing_group)
        
        # Кнопки OK/Cancel
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _browse_tesseract(self):
        """Открыть диалог выбора файла tesseract.exe."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите tesseract.exe",
            "",
            "Исполняемые файлы (*.exe);;Все файлы (*)",
        )
        if file_path:
            self._tesseract_path_edit.setText(file_path)
    
    def _save_settings(self):
        """Сохранить настройки в конфигурацию."""
        # Сохранить путь к Tesseract
        tesseract_path = self._tesseract_path_edit.text().strip()
        self.config.set_tesseract_path(tesseract_path)
        
        # Сохранить настройки предобработки
        self.config.set_osd_enabled(self._osd_checkbox.isChecked())
        self.config.set_deskew_enabled(self._deskew_checkbox.isChecked())
        
        self.accept()
