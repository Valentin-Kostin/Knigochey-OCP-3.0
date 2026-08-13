"""
GUI module for the OCR application.
Provides the main window and widgets using PySide6.
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
