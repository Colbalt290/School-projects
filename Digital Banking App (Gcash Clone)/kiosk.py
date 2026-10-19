import sys
from PyQt6.QtWidgets import QApplication
from ui.theme import apply_aurion_theme
from ui.kiosk import AurionKioskTerminal

if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_aurion_theme(app)

    kiosk = AurionKioskTerminal()
    kiosk.show()
    sys.exit(app.exec())