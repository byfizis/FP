import os
from PyQt6.QtGui import QIcon

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ICON_FILENAME = "photo_2025-11-12_09-38-13.jpg"
APP_ICON_PATH = os.path.join(BASE_DIR, "..", APP_ICON_FILENAME)


def get_app_icon():
    try:
        if os.path.exists(APP_ICON_PATH):
            return QIcon(APP_ICON_PATH)
    except Exception:
        pass
    return QIcon()


def format_time(milliseconds):
    seconds = milliseconds // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"