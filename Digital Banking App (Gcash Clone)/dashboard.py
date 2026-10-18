from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QListWidget, QGroupBox, QFormLayout, QGridLayout, QToolButton, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from db import bank_db

class ReceiptDialog(QDialog):
    """Pop-up modal displaying full receipt details upon transaction completion."""
    def __init__(self, receipt_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transaction Receipt")
        self.setFixedSize(300, 260)

        layout = QVBoxLayout()
        title = QLabel("--- AURION RECEIPT ---")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #0055FF;")
        layout.addWidget(title)

        form = QFormLayout()
        form.addRow("Type:", QLabel(receipt_data["type"]))
        form.addRow("Recipient/Target:", QLabel(receipt_data["recipient"]))
        form.addRow("Amount:", QLabel(f"PHP {receipt_data['amount']:,.2f}"))
        form.addRow("Timestamp:", QLabel(receipt_data["timestamp"]))
        form.addRow("Ref Number:", QLabel(receipt_data["ref_num"]))
        layout.addLayout(form)

        close_btn = QPushButton("Close Receipt")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)


class DashboardScreen(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurion - Dashboard")
        self.setFixedSize(380, 580)
        self.current_user = None

        main_layout = QVBoxLayout()

        # Balance Section
        self.welcome_label = QLabel("Welcome back!")
        self.welcome_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(self.welcome_label)

        self.balance_label = QLabel("PHP 0.00")
        self.balance_label.setStyleSheet("font-size: 26px; font-weight: bold; color: #0055FF;")
        main_layout.addWidget(self.balance_label)

        # Actions Grid (Cash In, Cash Out, Send, Payment)
        grid_box = QGroupBox("Services")
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)

        actions = [
            ("Cash In", "icons/cashin.png", self.handle_cash_in),
            ("Cash Out", "icons/cashout.png", self.handle_cash_out),
            ("Send", "icons/send.png", self.handle_send),
            ("Payment", "icons/pay.png", self.handle_payment),
        ]

        for index, (label, icon_path, handler) in enumerate(actions):
            row = index // 2
            col = index % 2
            btn = self.create_action_button(label, icon_path)
            btn.clicked.connect(handler)
            grid_layout.addWidget(btn, row, col)

        grid_box.setLayout(grid_layout)
        main_layout.addWidget(grid_box)

        # Inbox / Notifications
        inbox_box = QGroupBox("Inbox")
        inbox_layout = QVBoxLayout()
        self.inbox_list = QListWidget()
        inbox_layout.addWidget(self.inbox_list)
        inbox_box.setLayout(inbox_layout)
        main_layout.addWidget(inbox_box)

        # Logout Button
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.handle_logout)
        main_layout.addWidget(self.logout_btn)

        self.setLayout(main_layout)

    def create_action_button(self, text, icon_path):
        btn = QToolButton()
        btn.setText(text)
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn.setIconSize(QSize(36, 36))
        btn.setIcon(QIcon(icon_path))
        btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #DDDDDD;
                border-radius: 10px;
                background-color: #F8F9FA;
                font-size: 12px;
                font-weight: bold;
                color: #333333;
                padding: 10px;
                width: 120px;
            }
            QToolButton:hover {
                background-color: #EBF3FF;
                border: 1px solid #0055FF;
                color: #0055FF;
            }
        """)
        return btn

    def open_dashboard(self, username):
        self.current_user = username
        actual_bal = bank_db.getbal(username)
        self.welcome_label.setText(f"Welcome back, {username}!")
        self.balance_label.setText(f"PHP {actual_bal:,.2f}")
        self.refresh_inbox()
        self.show()

    def refresh_inbox(self):
        self.inbox_list.clear()
        messages = bank_db.get_inbox(self.current_user)
        if not messages:
            self.inbox_list.addItem("No notifications yet.")
        else:
            for msg in messages:
                self.inbox_list.addItem(msg)

    def show_receipt(self, receipt_data):
        receipt_dialog = ReceiptDialog(receipt_data, self)
        receipt_dialog.exec()

    # Handlers
    def handle_cash_in(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Cash In")
        layout = QVBoxLayout()
        amt_in = QLineEdit()
        amt_in.setPlaceholderText("Amount (PHP)")
        btn = QPushButton("Confirm Cash In")
        layout.addWidget(amt_in)
        layout.addWidget(btn)
        dialog.setLayout(layout)

        def run():
            try:
                amt = float(amt_in.text().strip())
                ok, new_bal, receipt = bank_db.cash_in(self.current_user, amt)
                if ok:
                    self.balance_label.setText(f"PHP {new_bal:,.2f}")
                    dialog.accept()
                    self.show_receipt(receipt)
                else:
                    QMessageBox.warning(dialog, "Error", new_bal)
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Invalid number.")

        btn.clicked.connect(run)
        dialog.exec()

    def handle_cash_out(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Cash Out")
        layout = QVBoxLayout()
        amt_in = QLineEdit()
        amt_in.setPlaceholderText("Amount (PHP)")
        btn = QPushButton("Confirm Cash Out")
        layout.addWidget(amt_in)
        layout.addWidget(btn)
        dialog.setLayout(layout)

        def run():
            try:
                amt = float(amt_in.text().strip())
                ok, new_bal, receipt = bank_db.cash_out(self.current_user, amt)
                if ok:
                    self.balance_label.setText(f"PHP {new_bal:,.2f}")
                    dialog.accept()
                    self.show_receipt(receipt)
                else:
                    QMessageBox.warning(dialog, "Error", new_bal)
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Invalid number.")

        btn.clicked.connect(run)
        dialog.exec()

    def handle_send(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Send Money")
        layout = QFormLayout()
        rec_in = QLineEdit()
        rec_in.setPlaceholderText("Recipient Username")
        amt_in = QLineEdit()
        amt_in.setPlaceholderText("Amount (PHP)")
        btn = QPushButton("Confirm Send")
        layout.addRow("Recipient:", rec_in)
        layout.addRow("Amount:", amt_in)
        layout.addRow(btn)
        dialog.setLayout(layout)

        def run():
            try:
                rec = rec_in.text().strip()
                amt = float(amt_in.text().strip())
                ok, new_bal, receipt = bank_db.send_money(self.current_user, rec, amt)
                if ok:
                    self.balance_label.setText(f"PHP {new_bal:,.2f}")
                    self.refresh_inbox()
                    dialog.accept()
                    self.show_receipt(receipt)
                else:
                    QMessageBox.warning(dialog, "Error", new_bal)
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Invalid number.")

        btn.clicked.connect(run)
        dialog.exec()

    def handle_payment(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Payment")
        layout = QFormLayout()
        biller_in = QLineEdit()
        biller_in.setPlaceholderText("Biller / Merchant Name")
        amt_in = QLineEdit()
        amt_in.setPlaceholderText("Amount (PHP)")
        btn = QPushButton("Confirm Payment")
        layout.addRow("Biller:", biller_in)
        layout.addRow("Amount:", amt_in)
        layout.addRow(btn)
        dialog.setLayout(layout)

        def run():
            try:
                biller = biller_in.text().strip()
                amt = float(amt_in.text().strip())
                ok, new_bal, receipt = bank_db.pay_bill(self.current_user, biller, amt)
                if ok:
                    self.balance_label.setText(f"PHP {new_bal:,.2f}")
                    dialog.accept()
                    self.show_receipt(receipt)
                else:
                    QMessageBox.warning(dialog, "Error", new_bal)
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Invalid number.")

        btn.clicked.connect(run)
        dialog.exec()

    def handle_logout(self):
        reply = QMessageBox.question(
            self, 'Confirm Logout', 'Are you sure you want to log out?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.hide()
            self.logout_requested.emit()