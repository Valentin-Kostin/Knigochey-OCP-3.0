"""
Main window for the OCR application.
Provides the complete GUI with all controls and functionality.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QToolBar,
    QMenuBar,
    QMenu,
    QStatusBar,
    QMessageBox,
    QFileDialog,
    QApplication,
    QLabel,
    QPushButton,
    QFrame,
)
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtCore import Qt, QThread, Signal

from ..engine import OCREngine, OCRResult, TesseractEngine, KrakenEngine, TrOCREngine
from ..preprocessing import PreprocessingPipeline, PipelineConfig
from .widgets import (
    ImagePreviewWidget,
    TextEditorWidget,
    EngineSelectorWidget,
    PreprocessingOptionsWidget,
    StatusBarWidget,
)


class OCRWorker(QThread):
    """Worker thread for OCR processing."""
    
    finished = Signal(OCRResult)
    error = Signal(str)
    progress = Signal(int)  # 0-100
    
    def __init__(
        self,
        engine: OCREngine,
        image_path: Path,
        model_name: Optional[str] = None,
        pipeline: Optional[PreprocessingPipeline] = None,
    ):
        """Initialize OCR worker."""
        super().__init__()
        self.engine = engine
        self.image_path = image_path
        self.model_name = model_name
        self.pipeline = pipeline
    
    def run(self) -> None:
        """Run OCR processing in background thread."""
        try:
            self.progress.emit(10)
            
            # Apply preprocessing if pipeline provided
            if self.pipeline:
                self.progress.emit(20)
                # Create temporary file for preprocessed image
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                
                try:
                    processed_image = self.pipeline.process_file(self.image_path, tmp_path)
                    process_path = tmp_path
                except Exception:
                    process_path = self.image_path
            else:
                process_path = self.image_path
            
            self.progress.emit(50)
            
            # Run OCR
            result = self.engine.recognize(process_path, self.model_name)
            
            # Cleanup temp file
            if self.pipeline and 'tmp_path' in locals():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            
            self.progress.emit(100)
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        self.setWindowTitle("Historical Slavic OCR")
        self.setMinimumSize(1200, 800)
        
        # Initialize engines
        self._engines: dict[str, OCREngine] = {
            "tesseract": TesseractEngine(),
            "kraken": KrakenEngine(),
            "trocr": TrOCREngine(),
        }
        
        self._current_engine: Optional[OCREngine] = None
        self._current_pipeline: Optional[PreprocessingPipeline] = None
        self._current_image_path: Optional[Path] = None
        self._last_export_dir: Optional[Path] = None
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._connect_signals()
        
        # Initialize engine selector
        self._update_engine_selector()
        
        # Set status
        self._status_bar.set_message("Ready - Load an image to begin")
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top section: Engine and preprocessing controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        
        # Engine selector
        self._engine_selector = EngineSelectorWidget()
        self._engine_selector.setMaximumWidth(350)
        controls_layout.addWidget(self._engine_selector)
        
        # Preprocessing options
        self._preprocessing_options = PreprocessingOptionsWidget()
        self._preprocessing_options.setMaximumWidth(300)
        controls_layout.addWidget(self._preprocessing_options)
        
        # Process button
        button_layout = QVBoxLayout()
        
        self._process_btn = QPushButton("🔍 Recognize Text")
        self._process_btn.setMinimumHeight(40)
        self._process_btn.setEnabled(False)
        button_layout.addWidget(self._process_btn)
        
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._clear_all)
        button_layout.addWidget(self._clear_btn)
        
        button_layout.addStretch()
        controls_layout.addLayout(button_layout)
        
        main_layout.addLayout(controls_layout)
        
        # Splitter for image and text
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)
        
        # Left: Image preview
        self._image_preview = ImagePreviewWidget()
        splitter.addWidget(self._image_preview)
        
        # Right: Text editor
        self._text_editor = TextEditorWidget()
        splitter.addWidget(self._text_editor)
        
        # Set initial sizes (50/50)
        splitter.setSizes([600, 600])
        
        main_layout.addWidget(splitter, 1)
        
        # Status bar at bottom
        self._status_bar = StatusBarWidget()
        main_layout.addWidget(self._status_bar)
    
    def _setup_menu(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Image", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_image)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_txt_action = QAction("Export as &TXT", self)
        export_txt_action.triggered.connect(lambda: self._export_text("txt"))
        file_menu.addAction(export_txt_action)
        
        export_docx_action = QAction("Export as &DOCX", self)
        export_docx_action.triggered.connect(lambda: self._export_text("docx"))
        file_menu.addAction(export_docx_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self._text_editor.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self._text_editor.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self._text_editor.selectAll)
        edit_menu.addAction(select_all_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._image_preview._zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._image_preview._zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("&Reset Zoom", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.triggered.connect(lambda: setattr(self._image_preview, '_zoom_factor', 1.0) or self._image_preview._update_display())
        view_menu.addAction(reset_zoom_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self) -> None:
        """Setup toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        open_action = QAction("📁 Open", self)
        open_action.setToolTip("Open image file")
        open_action.triggered.connect(self._open_image)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        process_action = QAction("🔍 Recognize", self)
        process_action.setToolTip("Recognize text in image")
        process_action.triggered.connect(self._run_ocr)
        toolbar.addAction(process_action)
        
        toolbar.addSeparator()
        
        export_action = QAction("💾 Export", self)
        export_action.setToolTip("Export recognized text")
        export_action.triggered.connect(lambda: self._export_text("txt"))
        toolbar.addAction(export_action)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Engine selector
        self._engine_selector.engine_changed.connect(self._on_engine_changed)
        self._engine_selector.model_changed.connect(self._on_model_changed)
        
        # Preprocessing options
        self._preprocessing_options.options_changed.connect(self._on_preprocessing_changed)
        
        # Buttons
        self._process_btn.clicked.connect(self._run_ocr)
        
        # Image preview
        self._image_preview.image_loaded.connect(self._on_image_loaded)
    
    def _update_engine_selector(self) -> None:
        """Update engine selector with available engines."""
        engines = [
            (name, engine.is_ready())
            for name, engine in self._engines.items()
        ]
        self._engine_selector.populate_engines(engines)
        
        # Select first available engine
        for name, available in engines:
            if available:
                self._on_engine_changed(name)
                break
    
    def _on_engine_changed(self, engine_name: str) -> None:
        """Handle engine selection change."""
        if engine_name not in self._engines:
            return
        
        engine = self._engines[engine_name]
        self._current_engine = engine
        
        if engine.is_ready():
            models = engine.get_available_models()
            self._engine_selector.populate_models(models)
            self._engine_selector.set_status("Ready", True)
        else:
            self._engine_selector.populate_models([])
            self._engine_selector.set_status("Not available", False)
    
    def _on_model_changed(self, model_name: str) -> None:
        """Handle model selection change."""
        pass  # Model is used during OCR execution
    
    def _on_preprocessing_changed(self) -> None:
        """Handle preprocessing options change."""
        config_dict = self._preprocessing_options.get_config()
        
        # Map to PipelineConfig
        if all(not v for v in config_dict.values()):
            self._current_pipeline = None
        else:
            from ..preprocessing import ProcessorConfig
            
            config = PipelineConfig(
                denoise=ProcessorConfig(enabled=config_dict["denoise"]),
                clahe=ProcessorConfig(enabled=config_dict["clahe"]),
                deskew=ProcessorConfig(enabled=config_dict["deskew"]),
                contrast=ProcessorConfig(enabled=config_dict["contrast"]),
                binarization=ProcessorConfig(enabled=config_dict["binarization"]),
            )
            self._current_pipeline = PreprocessingPipeline(config)
    
    def _on_image_loaded(self, image_path: str) -> None:
        """Handle image loaded event."""
        self._current_image_path = Path(image_path)
        self._process_btn.setEnabled(True)
        self._status_bar.set_message(f"Loaded: {Path(image_path).name}")
        self._status_bar.set_info(f"Size: {self._image_preview._original_pixmap.width()}x{self._image_preview._original_pixmap.height()}px")
    
    def _open_image(self) -> None:
        """Open image file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            str(self._last_export_dir or Path.home()),
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.gif);;All Files (*)",
        )
        
        if file_path:
            self._current_image_path = Path(file_path)
            if self._image_preview.load_image(self._current_image_path):
                self._process_btn.setEnabled(True)
                self._status_bar.set_message(f"Loaded: {self._current_image_path.name}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to load image: {file_path}")
    
    def _run_ocr(self) -> None:
        """Run OCR processing."""
        if not self._current_engine or not self._current_engine.is_ready():
            QMessageBox.warning(self, "Warning", "No OCR engine available")
            return
        
        if not self._current_image_path:
            QMessageBox.warning(self, "Warning", "No image loaded")
            return
        
        # Disable controls during processing
        self._process_btn.setEnabled(False)
        self._process_btn.setText("Processing...")
        self._status_bar.set_message("Processing...")
        self._status_bar.set_progress(0, show=True)
        
        # Get selected model
        model_name = self._engine_selector.get_selected_model()
        
        # Create worker
        self._worker = OCRWorker(
            engine=self._current_engine,
            image_path=self._current_image_path,
            model_name=model_name,
            pipeline=self._current_pipeline,
        )
        
        self._worker.finished.connect(self._on_ocr_finished)
        self._worker.error.connect(self._on_ocr_error)
        self._worker.progress.connect(self._status_bar.set_progress)
        
        self._worker.start()
    
    def _on_ocr_finished(self, result: OCRResult) -> None:
        """Handle OCR completion."""
        # Re-enable controls
        self._process_btn.setEnabled(True)
        self._process_btn.setText("🔍 Recognize Text")
        self._status_bar.set_progress(0, show=False)
        
        # Display result
        metadata = result.get_formatted_text().split('\n\n')[0] if '\n\n' in result.get_formatted_text() else ""
        self._text_editor.set_result_text(result.text, metadata)
        
        # Update status
        if result.has_warnings():
            warning_text = "; ".join(result.warnings)
            self._status_bar.set_message(f"Completed with warnings: {warning_text}")
        else:
            self._status_bar.set_message("Recognition completed successfully")
        
        # Show info
        info_parts = []
        if result.confidence > 0:
            info_parts.append(f"Confidence: {result.confidence:.1%}")
        if result.processing_time_ms > 0:
            info_parts.append(f"Time: {result.processing_time_ms:.1f}ms")
        if info_parts:
            self._status_bar.set_info(" | ".join(info_parts))
    
    def _on_ocr_error(self, error_msg: str) -> None:
        """Handle OCR error."""
        self._process_btn.setEnabled(True)
        self._process_btn.setText("🔍 Recognize Text")
        self._status_bar.set_progress(0, show=False)
        
        QMessageBox.critical(self, "OCR Error", f"Failed to recognize text:\n{error_msg}")
        self._status_bar.set_message("Error during recognition")
    
    def _export_text(self, format: str) -> None:
        """Export recognized text to file."""
        text = self._text_editor.get_text()
        
        if not text.strip():
            QMessageBox.information(self, "Info", "No text to export")
            return
        
        # Determine default filename
        if self._current_image_path:
            default_name = self._current_image_path.stem
        else:
            default_name = "ocr_result"
        
        # Get save path
        if format == "txt":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export as TXT",
                str(self._last_export_dir / f"{default_name}.txt") if self._last_export_dir else f"{default_name}.txt",
                "Text Files (*.txt);;All Files (*)",
            )
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    self._last_export_dir = Path(file_path).parent
                    self._status_bar.set_message(f"Exported to {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export: {e}")
        
        elif format == "docx":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export as DOCX",
                str(self._last_export_dir / f"{default_name}.docx") if self._last_export_dir else f"{default_name}.docx",
                "Word Documents (*.docx);;All Files (*)",
            )
            if file_path:
                try:
                    from docx import Document
                    
                    doc = Document()
                    
                    # Add metadata as paragraph with smaller font
                    lines = text.split('\n')
                    metadata_lines = []
                    content_start = 0
                    
                    for i, line in enumerate(lines):
                        if line.startswith(('Engine:', 'Model:', 'Confidence:', 'Processing time:')):
                            metadata_lines.append(line)
                            content_start = i + 1
                        else:
                            break
                    
                    if metadata_lines:
                        meta_para = doc.add_paragraph('\n'.join(metadata_lines))
                        for run in meta_para.runs:
                            run.font.size = doc.shared_styles['Normal'].font.size - 2
                    
                    # Add main content
                    content = '\n'.join(lines[content_start:])
                    if content.strip():
                        doc.add_paragraph(content)
                    
                    doc.save(file_path)
                    self._last_export_dir = Path(file_path).parent
                    self._status_bar.set_message(f"Exported to {file_path}")
                    
                except ImportError:
                    QMessageBox.warning(
                        self, 
                        "Missing Dependency", 
                        "python-docx is not installed. Install with: pip install python-docx"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export: {e}")
    
    def _clear_all(self) -> None:
        """Clear all content."""
        self._image_preview.clear()
        self._text_editor.clear()
        self._current_image_path = None
        self._process_btn.setEnabled(False)
        self._status_bar.reset()
        self._status_bar.set_message("Ready - Load an image to begin")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Historical Slavic OCR",
            "Historical Slavic OCR Application\n\n"
            "A tool for recognizing historical Slavic texts using multiple OCR engines:\n"
            "• Tesseract OCR - For printed texts\n"
            "• Kraken OCR - Specialized for historical documents\n"
            "• TrOCR - Transformer-based advanced recognition\n\n"
            "Features:\n"
            "• Multi-engine support with automatic fallback\n"
            "• Advanced image preprocessing\n"
            "• Support for various Slavic languages\n"
            "• Export to TXT and DOCX formats\n\n"
            "© 2024"
        )
