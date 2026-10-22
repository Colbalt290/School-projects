import sys
from PyQt6.QtWidgets import QMessageBox, QWidget, QApplication, QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSlot

class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = "PyQt Button"
        self.x = 200
        self.y = 200
        self.width = 300
        self.height = 300
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.x, self.y, self.width, self.height)
        self.setWindowIcon(QIcon('pythonico.ico'))

        self.button = QPushButton('Click me!', self)
        self.button.setToolTip("You've hovered over me!")
        self.button.move(100, 70)
        self.button.clicked.connect(self.clickMe)

        self.show()

    @pyqtSlot()
    def clickMe(self):
        # Updated enum syntax for PyQt6: StandardButton.Yes, StandardButton.No, etc.
        buttonReply = QMessageBox.question(
            self, 
            "Testing Response", 
            "Do you like PyQt6?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.Yes
        )
        
        if buttonReply == QMessageBox.StandardButton.Yes:
            QMessageBox.warning(
                self, 
                "Evaluation", 
                "User clicked Yes", 
                QMessageBox.StandardButton.Ok
            )
        else:
            QMessageBox.information(
                self, 
                "Evaluation", 
                "User clicked No", 
                QMessageBox.StandardButton.Ok
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec())