import os
from PyQt6.QtGui import QIcon

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS_DIR = os.path.join(PROJECT_ROOT, "icons")
QSS_PATH = os.path.join(PROJECT_ROOT, "style.qss")
LOGO_PATH = os.path.join(ICONS_DIR, "logo.png")


def apply_aurion_theme(app):
    """Enforces neutral Fusion base engine and applies the shared QSS theme."""
    app.setStyle("Fusion")

    if os.path.exists(QSS_PATH):
        with open(QSS_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        print("Loaded style.qss successfully.")
    else:
        print(f"Warning: style.qss not found at {QSS_PATH}")

    if os.path.exists(LOGO_PATH):
        app.setWindowIcon(QIcon(LOGO_PATH))

