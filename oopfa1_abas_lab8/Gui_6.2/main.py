import sys
from PyQt6.QtWidgets import QApplication
from registration import RegistrationWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RegistrationWindow()
    sys.exit(app.exec())