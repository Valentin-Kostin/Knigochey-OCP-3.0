"""
Модуль графического интерфейса для OCR-приложения.
Предоставляет главное окно и виджеты с использованием PySide6.
"""

from .main_window import MainWindow
from .widgets import (
    ImagePreviewWidget,
    TextEditorWidget,
    EngineSelectorWidget,
    PreprocessingOptionsWidget,
    StatusBarWidget,
)

__all__ = [
    "MainWindow",
    "ImagePreviewWidget",
    "TextEditorWidget",
    "EngineSelectorWidget",
    "PreprocessingOptionsWidget",
    "StatusBarWidget",
]
