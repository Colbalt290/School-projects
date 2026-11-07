#!/usr/bin/env python3
"""
BinTimer — Modern Rubik's Cube Timer & Battle Arena
═════════════════════════════════════════════════════
Application entry point. Initializes QApplication, loads the QSS theme,
and starts the persistent root window.

Usage:
    python3 main.py
"""

from __future__ import annotations

import os
import sys

# Ensure both the project directory and package root are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
for _p in (PARENT_DIR, BASE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QApplication

try:
    from bintimer.main_window import MainWindow
except ImportError:
    from main_window import MainWindow

_QSS_CANDIDATES = [
    os.path.join(BASE_DIR, "UI", "style.qss"),
    os.path.join(BASE_DIR, "style.qss"),
    os.path.join(BASE_DIR, "UI", "style.qss.txt"),
]


def _load_stylesheet(app: QApplication) -> None:
    """Load the first matching QSS file."""
    for path in _QSS_CANDIDATES:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    app.setStyleSheet(f.read())
                print(f"[BinTimer] Successfully loaded stylesheet: {path}")
                return
            except Exception as e:
                print(f"[BinTimer] Error reading stylesheet {path}: {e}")
    print("[BinTimer] Note: No stylesheet found, using default Qt theme.")


def main() -> None:
    # High-DPI support
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("BinTimer")
    app.setOrganizationName("BinTimer")

    _load_stylesheet(app)

    window = MainWindow(BASE_DIR)
    window.showMaximized()

    # F11: Toggle Fullscreen
    f11 = QShortcut(QKeySequence(Qt.Key.Key_F11), window)
    f11.activated.connect(
        lambda: window.showNormal() if window.isFullScreen() else window.showFullScreen()
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
