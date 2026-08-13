# Historical Slavic OCR Application

A GUI application for recognizing historical Slavic texts using multiple OCR engines with advanced image preprocessing.

## Features

- **Multi-engine support**: 
  - Tesseract OCR - Fast, universal OCR with Slavic language support
  - Kraken OCR - Specialized for historical documents and manuscripts
  - TrOCR - Transformer-based advanced recognition

- **Advanced preprocessing**:
  - Denoising (bilateral filter, non-local means)
  - Contrast enhancement (CLAHE)
  - Deskewing
  - Binarization (Otsu, adaptive thresholding)
  - Configurable presets for different document types

- **User-friendly GUI**:
  - Two-panel interface (image preview + text editor)
  - Image zoom controls
  - Real-time processing status
  - Editable OCR results
  - Export to TXT and DOCX formats

- **Historical text support**:
  - Multiple Slavic languages
  - Old printed texts
  - Handwritten manuscripts
  - Low-quality scans

## Installation

### Requirements

- Python 3.9+
- PySide6
- Pillow
- NumPy
- OpenCV (optional, for advanced preprocessing)

### Optional Dependencies

- pytesseract + tesseract-ocr (for Tesseract engine)
- kraken (for Kraken engine)
- transformers + torch (for TrOCR engine)
- python-docx (for DOCX export)

### Install Commands

```bash
# Core dependencies
pip install PySide6 Pillow numpy

# Optional: OpenCV for preprocessing
pip install opencv-python

# Optional: Tesseract OCR
pip install pytesseract
# Also install tesseract-ocr system package:
# Ubuntu/Debian: sudo apt install tesseract-ocr
# macOS: brew install tesseract
# Windows: Download from https://github.com/tesseract-ocr/tesseract

# Optional: Kraken OCR
pip install kraken

# Optional: TrOCR (Transformer-based)
pip install transformers torch torchvision

# Optional: DOCX export
pip install python-docx
```

## Usage

### Launch the Application

```bash
python -m ocr_app.main
```

Or directly:

```bash
python ocr_app/main.py
```

### Basic Workflow

1. **Open Image**: Click "Open" or use File → Open Image
2. **Select Engine**: Choose from available OCR engines
3. **Configure Preprocessing**: Select preset or customize options
4. **Recognize**: Click "Recognize Text" button
5. **Edit**: Review and edit the recognized text
6. **Export**: Save as TXT or DOCX

### Preprocessing Presets

- **Default**: CLAHE + contrast enhancement
- **Old Printed Text**: Denoise + CLAHE + deskew + enhanced contrast
- **Handwritten**: NL-means denoise + CLAHE + deskew
- **Low Quality Scan**: All enhancements enabled

## Project Structure

```
ocr_app/
├── __init__.py          # Package info
├── main.py              # Application entry point
├── engine/              # OCR engines
│   ├── __init__.py
│   ├── base.py          # Base classes
│   ├── tesseract_engine.py
│   ├── kraken_engine.py
│   └── trocr_engine.py
├── preprocessing/       # Image preprocessing
│   ├── __init__.py
│   ├── processors.py    # Individual processors
│   └── pipeline.py      # Processing pipeline
├── gui/                 # Graphical interface
│   ├── __init__.py
│   ├── main_window.py   # Main window
│   └── widgets.py       # Custom widgets
└── data/
    └── models/          # Custom models directory
```

## Architecture

The application follows a modular architecture:

1. **Engine Layer**: Abstract base class with implementations for each OCR engine
2. **Preprocessing Layer**: Configurable pipeline of image enhancement processors
3. **GUI Layer**: PySide6-based interface with custom widgets
4. **Worker Thread**: Background processing to keep UI responsive

## Supported Formats

### Input Images
- PNG, JPG, JPEG, BMP, TIFF, GIF

### Output
- TXT (UTF-8 encoded)
- DOCX (Microsoft Word)

## Tips for Best Results

1. **For old printed texts**: Use "Old Printed Text" preset with Tesseract
2. **For manuscripts**: Use "Handwritten" preset with Kraken or TrOCR
3. **For low quality scans**: Use "Low Quality Scan" preset
4. **For mixed content**: Try multiple engines and compare results

## Troubleshooting

### No engines available
- Install at least one OCR engine (Tesseract recommended for beginners)
- Check system PATH for tesseract executable

### Poor recognition quality
- Try different preprocessing presets
- Ensure image is not too small (minimum 300 DPI recommended)
- Try a different OCR engine

### Memory issues with TrOCR
- TrOCR models are large; use smaller models for limited RAM
- Consider using CPU instead of GPU for smaller models

## License

This project is provided as-is for educational and research purposes.

## Contributing

Contributions welcome! Please ensure:
- Type hints on all functions
- Docstrings for all classes and methods
- Follow existing code style
