"""
Модуль управления конфигурацией приложения.
Отвечает за чтение и сохранение настроек в config.ini.
"""
import os
import configparser
from pathlib import Path


class ConfigManager:
    """Управление настройками приложения через INI-файл."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.ini"
        
        self.config_path = Path(config_path)
        self.config = configparser.ConfigParser()
        self._load()
    
    def _load(self):
        """Загрузка конфигурации из файла."""
        if self.config_path.exists():
            self.config.read(self.config_path, encoding='utf-8')
        else:
            self._save()  # Создать файл с настройками по умолчанию
    
    def _save(self):
        """Сохранение конфигурации в файл."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get_tesseract_path(self) -> str:
        """Получить путь к tesseract.exe."""
        return self.config.get('paths', 'tesseract_exe', fallback='')
    
    def set_tesseract_path(self, path: str):
        """Установить путь к tesseract.exe."""
        if not self.config.has_section('paths'):
            self.config.add_section('paths')
        self.config.set('paths', 'tesseract_exe', path)
        self._save()
    
    def get_last_engine(self) -> str:
        """Получить последний использованный движок."""
        return self.config.get('settings', 'last_engine', fallback='tesseract')
    
    def set_last_engine(self, engine: str):
        """Установить последний использованный движок."""
        if not self.config.has_section('settings'):
            self.config.add_section('settings')
        self.config.set('settings', 'last_engine', engine)
        self._save()
    
    def get_use_gpu(self) -> bool:
        """Получить настройку использования GPU."""
        return self.config.getboolean('settings', 'use_gpu', fallback=False)
    
    def set_use_gpu(self, use_gpu: bool):
        """Установить настройку использования GPU."""
        if not self.config.has_section('settings'):
            self.config.add_section('settings')
        self.config.set('settings', 'use_gpu', str(use_gpu))
        self._save()
    
    def get_deskew_enabled(self) -> bool:
        """Получить настройку выравнивания."""
        return self.config.getboolean('settings', 'deskew_enabled', fallback=True)
    
    def set_deskew_enabled(self, enabled: bool):
        """Установить настройку выравнивания."""
        if not self.config.has_section('settings'):
            self.config.add_section('settings')
        self.config.set('settings', 'deskew_enabled', str(enabled))
        self._save()
    
    def get_osd_enabled(self) -> bool:
        """Получить настройку определения ориентации."""
        return self.config.getboolean('settings', 'osd_enabled', fallback=True)
    
    def set_osd_enabled(self, enabled: bool):
        """Установить настройку определения ориентации."""
        if not self.config.has_section('settings'):
            self.config.add_section('settings')
        self.config.set('settings', 'osd_enabled', str(enabled))
        self._save()
    
    def get_window_width(self) -> int:
        """Получить ширину окна."""
        return self.config.getint('window', 'width', fallback=1200)
    
    def get_window_height(self) -> int:
        """Получить высоту окна."""
        return self.config.getint('window', 'height', fallback=800)
    
    def set_window_size(self, width: int, height: int):
        """Установить размер окна."""
        if not self.config.has_section('window'):
            self.config.add_section('window')
        self.config.set('window', 'width', str(width))
        self.config.set('window', 'height', str(height))
        self._save()
