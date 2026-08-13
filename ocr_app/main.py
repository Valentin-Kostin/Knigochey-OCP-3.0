#!/usr/bin/env python3
"""
Точка входа для приложения распознавания исторических славянских текстов.
Запускает графический интерфейс приложения.
"""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ocr_app.gui.main_window import MainWindow


def main():
    """Основная точка входа приложения."""
    # Включаем масштабирование High DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Создаём приложение
    app = QApplication(sys.argv)
    app.setApplicationName("Historical Slavic OCR")
    app.setOrganizationName("OCR Team")
    
    # Устанавливаем шрифт приложения
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Устанавливаем стиль
    app.setStyle("Fusion")
    
    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем приложение
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
