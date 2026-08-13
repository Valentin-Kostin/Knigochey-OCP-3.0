"""
Custom widgets for the OCR application GUI.
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
    """Widget for displaying image preview with zoom and pan."""
    
    image_loaded = Signal(str)  # Emits file path when image is loaded
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize image preview widget."""
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self._current_image_path: Optional[Path] = None
        self._pixmap: Optional[QPixmap] = None
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(200, 150)
        self._label.setText("No image loaded")
        self._label.setStyleSheet("QLabel { color: gray; }")
        
        layout.addWidget(self._label)
        
        # Zoom controls
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
        Load an image for preview.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            True if successful, False otherwise.
        """
        if not image_path.exists():
            return False
        
        self._current_image_path = image_path
        self._original_pixmap = QPixmap(str(image_path))
        
        if self._original_pixmap.isNull():
            self._label.setText("Failed to load image")
            return False
        
        self._zoom_factor = 1.0
        self._update_display()
        
        self._zoom_in_btn.setEnabled(True)
        self._zoom_out_btn.setEnabled(True)
        
        self.image_loaded.emit(str(image_path))
        return True
    
    def clear(self) -> None:
        """Clear the current image."""
        self._current_image_path = None
        self._pixmap = None
        self._original_pixmap = None
        self._zoom_factor = 1.0
        
        self._label.clear()
        self._label.setText("No image loaded")
        self._label.setStyleSheet("QLabel { color: gray; }")
        self._zoom_label.setText("100%")
        self._zoom_in_btn.setEnabled(False)
        self._zoom_out_btn.setEnabled(False)
    
    def _update_display(self) -> None:
        """Update the displayed pixmap based on zoom factor."""
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
        """Zoom in the image."""
        if self._zoom_factor < 5.0:
            self._zoom_factor *= 1.25
            self._update_display()
    
    def _zoom_out(self) -> None:
        """Zoom out the image."""
        if self._zoom_factor > 0.2:
            self._zoom_factor /= 1.25
            self._update_display()
    
    def get_current_image_path(self) -> Optional[Path]:
        """Get the current image path."""
        return self._current_image_path


class TextEditorWidget(QTextEdit):
    """Text editor widget for displaying and editing OCR results."""
    
    text_changed = Signal()  # Emitted when text is modified
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize text editor widget."""
        super().__init__(parent)
        
        # Set monospace font for better readability
        font = QFont("Courier New", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Enable line wrapping
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # Set placeholder text
        self.setPlaceholderText("OCR result will appear here...\n\nYou can edit this text before exporting.")
        
        # Connect signal
        self.textChanged.connect(self.text_changed.emit)
    
    def set_result_text(self, text: str, metadata: Optional[str] = None) -> None:
        """
        Set the OCR result text with optional metadata.
        
        Args:
            text: The recognized text.
            metadata: Optional metadata header.
        """
        if metadata:
            self.setPlainText(f"{metadata}\n\n{text}")
        else:
            self.setPlainText(text)
    
    def clear(self) -> None:
        """Clear the text editor."""
        self.clear()
        self.setPlaceholderText("OCR result will appear here...\n\nYou can edit this text before exporting.")
    
    def get_text(self) -> str:
        """Get the current text content."""
        return self.toPlainText()


class EngineSelectorWidget(QGroupBox):
    """Widget for selecting OCR engine and model."""
    
    engine_changed = Signal(str)  # Emits engine name
    model_changed = Signal(str)   # Emits model name
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize engine selector widget."""
        super().__init__("OCR Engine", parent)
        
        layout = QVBoxLayout(self)
        
        # Engine selection
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("Engine:"))
        
        self._engine_combo = QComboBox()
        self._engine_combo.setMinimumWidth(200)
        self._engine_combo.currentTextChanged.connect(self._on_engine_changed)
        engine_layout.addWidget(self._engine_combo)
        engine_layout.addStretch()
        
        layout.addLayout(engine_layout)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(200)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        model_layout.addWidget(self._model_combo)
        model_layout.addStretch()
        
        layout.addLayout(model_layout)
        
        # Engine status
        self._status_label = QLabel("Status: Not initialized")
        self._status_label.setStyleSheet("color: orange;")
        layout.addWidget(self._status_label)
        
        layout.addStretch()
    
    def populate_engines(self, engines: list[tuple[str, bool]]) -> None:
        """
        Populate the engine combo box.
        
        Args:
            engines: List of (engine_name, is_available) tuples.
        """
        self._engine_combo.clear()
        
        for name, available in engines:
            status = "✓" if available else "✗"
            self._engine_combo.addItem(f"{status} {name}", userData=name)
        
        if self._engine_combo.count() > 0:
            self._engine_combo.setCurrentIndex(0)
    
    def populate_models(self, models: list[str]) -> None:
        """
        Populate the model combo box.
        
        Args:
            models: List of model names.
        """
        self._model_combo.clear()
        
        if not models:
            self._model_combo.addItem("No models available")
            self._model_combo.setEnabled(False)
        else:
            for model in models:
                self._model_combo.addItem(model)
            self._model_combo.setEnabled(True)
    
    def set_status(self, status: str, success: bool = True) -> None:
        """
        Set the engine status message.
        
        Args:
            status: Status message.
            success: Whether the status indicates success.
        """
        self._status_label.setText(f"Status: {status}")
        
        if success:
            self._status_label.setStyleSheet("color: green;")
        elif status == "Not initialized":
            self._status_label.setStyleSheet("color: orange;")
        else:
            self._status_label.setStyleSheet("color: red;")
    
    def get_selected_engine(self) -> Optional[str]:
        """Get the currently selected engine name."""
        return self._engine_combo.currentData()
    
    def get_selected_model(self) -> Optional[str]:
        """Get the currently selected model name."""
        if not self._model_combo.isEnabled():
            return None
        return self._model_combo.currentText()
    
    def _on_engine_changed(self, engine_name: str) -> None:
        """Handle engine selection change."""
        # Remove checkmark from display
        clean_name = engine_name.split(" ", 1)[-1] if " " in engine_name else engine_name
        self.engine_changed.emit(clean_name)
    
    def _on_model_changed(self, model_name: str) -> None:
        """Handle model selection change."""
        if model_name != "No models available":
            self.model_changed.emit(model_name)


class PreprocessingOptionsWidget(QGroupBox):
    """Widget for configuring preprocessing options."""
    
    options_changed = Signal()  # Emitted when any option changes
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize preprocessing options widget."""
        super().__init__("Preprocessing", parent)
        
        layout = QVBoxLayout(self)
        
        # Preset selection
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        
        self._preset_combo = QComboBox()
        self._preset_combo.addItem("Default", "default")
        self._preset_combo.addItem("Old Printed Text", "old_printed")
        self._preset_combo.addItem("Handwritten", "handwritten")
        self._preset_combo.addItem("Low Quality Scan", "low_quality")
        self._preset_combo.addItem("Custom", "custom")
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self._preset_combo)
        preset_layout.addStretch()
        
        layout.addLayout(preset_layout)
        
        # Individual options
        self._denoise_check = QCheckBox("Denoise")
        self._denoise_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._denoise_check)
        
        self._clahe_check = QCheckBox("Contrast Enhancement (CLAHE)")
        self._clahe_check.setChecked(True)
        self._clahe_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._clahe_check)
        
        self._deskew_check = QCheckBox("Deskew")
        self._deskew_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._deskew_check)
        
        self._contrast_check = QCheckBox("Contrast Adjustment")
        self._contrast_check.setChecked(True)
        self._contrast_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._contrast_check)
        
        self._binarize_check = QCheckBox("Binarization")
        self._binarize_check.stateChanged.connect(self._on_option_changed)
        layout.addWidget(self._binarize_check)
        
        layout.addStretch()
    
    def get_config(self) -> dict:
        """Get current preprocessing configuration."""
        return {
            "denoise": self._denoise_check.isChecked(),
            "clahe": self._clahe_check.isChecked(),
            "deskew": self._deskew_check.isChecked(),
            "contrast": self._contrast_check.isChecked(),
            "binarization": self._binarize_check.isChecked(),
        }
    
    def set_from_config(self, config: dict) -> None:
        """Set options from a configuration dictionary."""
        self._denoise_check.setChecked(config.get("denoise", False))
        self._clahe_check.setChecked(config.get("clahe", True))
        self._deskew_check.setChecked(config.get("deskew", False))
        self._contrast_check.setChecked(config.get("contrast", True))
        self._binarize_check.setChecked(config.get("binarization", False))
    
    def _on_preset_changed(self, index: int) -> None:
        """Handle preset selection change."""
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
        # Custom keeps current settings
        
        self.options_changed.emit()
    
    def _on_option_changed(self) -> None:
        """Handle individual option change."""
        self._preset_combo.setCurrentText("Custom")
        self.options_changed.emit()


class StatusBarWidget(QWidget):
    """Status bar widget showing progress and messages."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize status bar widget."""
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Status label
        self._status_label = QLabel("Ready")
        self._status_label.setMinimumWidth(200)
        layout.addWidget(self._status_label)
        
        # Progress bar
        self._progress = QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setMaximumWidth(200)
        self._progress.hide()
        layout.addWidget(self._progress)
        
        # Info label
        self._info_label = QLabel("")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._info_label)
    
    def set_message(self, message: str) -> None:
        """Set the status message."""
        self._status_label.setText(message)
    
    def set_progress(self, value: int, show: bool = True) -> None:
        """
        Set progress value.
        
        Args:
            value: Progress value (0-100).
            show: Whether to show the progress bar.
        """
        self._progress.setValue(value)
        if show:
            self._progress.show()
        else:
            self._progress.hide()
    
    def set_info(self, info: str) -> None:
        """Set the info text."""
        self._info_label.setText(info)
    
    def reset(self) -> None:
        """Reset the status bar to default state."""
        self._status_label.setText("Ready")
        self._progress.setValue(0)
        self._progress.hide()
        self._info_label.setText("")
