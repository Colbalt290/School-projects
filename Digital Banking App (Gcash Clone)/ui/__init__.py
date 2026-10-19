"""
Aurion UI Presentation Layer.
Contains all PyQt6/PySide6 widgets, dialogs, screens, and styling.
"""

from .login import LoginScreen, SignUpDialog
from .dashboard import DashboardScreen, ReceiptDialog
from .kiosk import AurionKioskTerminal, KioskReceiptDialog
from .theme import apply_aurion_theme

__all__ = [
    "LoginScreen",
    "SignUpDialog",
    "DashboardScreen",
    "ReceiptDialog",
    "AurionKioskTerminal",
    "KioskReceiptDialog",
    "apply_aurion_theme",
]

