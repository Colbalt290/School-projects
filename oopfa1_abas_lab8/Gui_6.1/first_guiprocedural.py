import sys
from PyQt6.QtWidgets import QApplication, QWidget

app = QApplication(sys.argv)
window = QWidget()
window.resize(200, 200)
window.move(30,30)
window.setWindowTitle('Abas First GUI')
window.show()
sys.exit(app.exec())