import sys
import os

# Ensure project root is in sys.path when running script directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QMessageBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from ui.theme import apply_aurion_theme
from core import bank_service


class KioskReceiptDialog(QDialog):
    """Dispense receipt popup shown at the physical kiosk."""
    def __init__(self, receipt_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kiosk Receipt")
        self.setFixedSize(320, 280)

        layout = QVBoxLayout()
        title = QLabel("CASH DISPENSED")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("aurionRole", "dialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.addRow("Terminal:", QLabel("Aurion Kiosk #001"))
        form.addRow("Account User:", QLabel(str(receipt_data.get("recipient", ""))))
        form.addRow("Amount Dispensed:", QLabel(f"PHP {receipt_data.get('amount', 0.0):,.2f}"))
        form.addRow("Timestamp:", QLabel(str(receipt_data.get("timestamp", ""))))
        form.addRow("Ref Number:", QLabel(str(receipt_data.get("ref_num", ""))))
        layout.addLayout(form)

        close_btn = QPushButton("Take Cash & Collect Receipt")
        close_btn.setObjectName("collectReceiptButton")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)


class AurionKioskTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurion Kiosk Terminal #001")
        self.setFixedSize(360, 520)

        main_layout = QVBoxLayout()

        # 1. Kiosk Digital Screen Header
        self.title_label = QLabel("WELCOME TO AURION KIOSK")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setProperty("aurionRole", "kioskBody")

        self.sub_label = QLabel("Please enter your 6-digit reference code:")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setProperty("aurionRole", "muted")

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.sub_label)

        # 2. Digital Code Display
        self.code_display = QLabel("______")
        self.code_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_display.setProperty("aurionRole", "referenceCode")
        main_layout.addWidget(self.code_display)

        # Buffer string for keypad entry
        self.current_code = ""

        # 3. ATM Keypad Grid (3x4)
        keypad_layout = QGridLayout()
        keypad_layout.setSpacing(10)

        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('CLEAR', 3, 0), ('0', 3, 1), ('DISPENSE', 3, 2)
        ]

        for text, row, col in buttons:
            btn = QPushButton(text)

            if text == 'CLEAR':
                btn.setObjectName("clearButton")
                btn.clicked.connect(self.handle_clear)
                self.clear_btn = btn
            elif text == 'DISPENSE':
                btn.setObjectName("dispenseButton")
                btn.clicked.connect(self.handle_dispense)
                self.dispense_btn = btn
            else:
                btn.setProperty("aurionRole", "keypadKey")
                btn.clicked.connect(lambda _, digit=text: self.handle_num_click(digit))

            keypad_layout.addWidget(btn, row, col)

        main_layout.addLayout(keypad_layout)
        self.setLayout(main_layout)

    def handle_num_click(self, digit):
        if len(self.current_code) < 6:
            self.current_code += digit
            self.update_display()

    def handle_clear(self):
        self.current_code = ""
        self.update_display()

    def update_display(self):
        padded = self.current_code.ljust(6, '_')
        self.code_display.setText(padded)

    def handle_dispense(self):
        if len(self.current_code) != 6:
            QMessageBox.warning(self, "Kiosk Error", "Please enter a full 6-digit reference code.")
            return

        success, message, receipt = bank_service.redeem_cashout_code(self.current_code)

        if success:
            receipt_dialog = KioskReceiptDialog(receipt, self)
            receipt_dialog.exec()
            self.handle_clear()
        else:
            QMessageBox.critical(self, "Transaction Failed", message)
            self.handle_clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_aurion_theme(app)

    kiosk = AurionKioskTerminal()
    kiosk.show()
    sys.exit(app.exec())

