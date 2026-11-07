#!/usr/bin/env python3
"""
BinTimer — Rubik's Cube Timer (Solo + PvP)
═══════════════════════════════════════════
Entry point.  Loads the external QSS stylesheet,
creates the main window, and launches it.

The window starts **maximized** (not fullscreen) so that it
is freely resizable on desktop.  Press F11 or double-click
the title bar to toggle fullscreen.

Usage:
    python main.py
"""

import os
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui     import QKeySequence, QShortcut
from PyQt6.QtCore    import Qt

from main_window import MainWindow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Possible stylesheet locations (checked in order)
_QSS_CANDIDATES = [
    os.path.join(BASE_DIR, "UI", "style.qss"),
    os.path.join(BASE_DIR, "style.qss"),
    os.path.join(BASE_DIR, "UI", "style.qss.txt"),
    os.path.join(BASE_DIR, "style.qss.txt"),
]


def _load_stylesheet(app: QApplication) -> None:
    """Load the first QSS file found from the candidate list."""
    for path in _QSS_CANDIDATES:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                app.setStyleSheet(fh.read())
            print(f"[BinTimer] Loaded stylesheet: {path}")
            return
    print("[BinTimer] Warning: no style.qss found — using Qt defaults")


def main() -> None:
    # High-DPI scaling (useful on touch devices)
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("BinTimer")
    app.setOrganizationName("BinTimer")

    _load_stylesheet(app)

    window = MainWindow(BASE_DIR)

    # Resizable desktop window — start maximized, not fullscreen
    window.showMaximized()

    # F11 toggles fullscreen
    f11 = QShortcut(QKeySequence(Qt.Key.Key_F11), window)
    f11.activated.connect(
        lambda: window.showNormal() if window.isFullScreen()
        else window.showFullScreen()
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
