from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from auth import auth
from db import bank_db

class SignUpDialog(QDialog):
    """Modal dialog for account registration."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aurion - Sign Up")
        self.setFixedSize(350, 260)
        
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.un_input = QLineEdit()
        self.email_input = QLineEdit()
        self.pword_input = QLineEdit()
        self.pword_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addRow("Full Name:", self.name_input)
        layout.addRow("Username:", self.un_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Password:", self.pword_input)
        layout.addRow("4-Digit PIN:", self.pin_input)
        
        self.msg_label = QLabel("")
        self.msg_label.setStyleSheet("color: red;")
        layout.addRow(self.msg_label)
        
        btn_layout = QHBoxLayout()
        self.register_btn = QPushButton("Register")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.register_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)
        
        self.setLayout(layout)
        
        self.register_btn.clicked.connect(self.handle_register)
        self.cancel_btn.clicked.connect(self.reject)

    def handle_register(self):
        name = self.name_input.text().strip()
        username = self.un_input.text().strip()
        email = self.email_input.text().strip()
        password = self.pword_input.text().strip()
        pin = self.pin_input.text().strip()

        if not all([name, username, email, password, pin]):
            self.msg_label.setText("Error: All fields are required.")
            return

        success = bank_db.create_account(username, name, email, password, pin)
        if success:
            QMessageBox.information(self, "Success", "Account created successfully! You can now login.")
            self.accept()
        else:
            self.msg_label.setText("Error: Username already exists.")


class LoginScreen(QWidget):
    # Signal emitted when login succeeds, passing the username to main.py
    login_successful = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurion - Login")
        self.setFixedSize(350, 220)
        
        layout = QVBoxLayout()
        
        title = QLabel("Welcome to Aurion")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        self.un_input = QLineEdit()
        self.pword_input = QLineEdit()
        self.pword_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("Username/Email:", self.un_input)
        form_layout.addRow("Password/PIN:", self.pword_input)
        layout.addLayout(form_layout)
        
        self.msg_label = QLabel("")
        self.msg_label.setStyleSheet("color: red;")
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.msg_label)
        
        btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.signup_btn = QPushButton("Sign Up")
        self.quit_btn = QPushButton("Quit")
        
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.signup_btn)
        btn_layout.addWidget(self.quit_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.login_btn.clicked.connect(self.handle_login)
        self.signup_btn.clicked.connect(self.open_signup)
        self.quit_btn.clicked.connect(self.close)

    def open_signup(self):
        signup_dialog = SignUpDialog(self)
        signup_dialog.exec()

    def handle_login(self):
        identifier = self.un_input.text().strip()
        secret = self.pword_input.text().strip()
        
        user = auth.verify_login(identifier, secret)
        if user:
            self.msg_label.setText("")
            self.login_successful.emit(user)
        else:
            self.msg_label.setText("Invalid credentials.")