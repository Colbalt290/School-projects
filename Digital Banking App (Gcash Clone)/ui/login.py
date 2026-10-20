import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QDialog, QFormLayout, QFrame,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
from .theme import LOGO_PATH, APP_ICON_PATH
from core import auth_service


class SignUpDialog(QDialog):
    """Modal dialog for account registration."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aurion - Sign Up")
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.setFixedSize(450, 490)

        layout = QFormLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        def make_field_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600; border: none; background: transparent;")
            return lbl

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("John Doe")
        self.name_input.setFixedHeight(42)

        self.un_input = QLineEdit()
        self.un_input.setPlaceholderText("johndoe")
        self.un_input.setFixedHeight(42)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("john@example.com")
        self.email_input.setFixedHeight(42)

        self.pword_input = QLineEdit()
        self.pword_input.setPlaceholderText("••••••••")
        self.pword_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pword_input.setFixedHeight(42)

        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("••••")
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setFixedHeight(42)

        layout.addRow(make_field_label("Full Name:"), self.name_input)
        layout.addRow(make_field_label("Username:"), self.un_input)
        layout.addRow(make_field_label("Email:"), self.email_input)
        layout.addRow(make_field_label("Password:"), self.pword_input)
        layout.addRow(make_field_label("4-Digit PIN:"), self.pin_input)

        self.msg_label = QLabel("")
        self.msg_label.setStyleSheet("color: #ff5555; font-size: 12px; border: none; background: transparent;")
        layout.addRow(self.msg_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.register_btn = QPushButton("Register")
        self.register_btn.setProperty("aurionRole", "primary")
        self.register_btn.setFixedHeight(42)
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(42)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_layout.addWidget(self.register_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)

        self.register_btn.clicked.connect(self.handle_register)
        self.cancel_btn.clicked.connect(self.reject)

    def handle_register(self):
        name = self.name_input.text().strip()
        username = self.un_input.text().strip()
        email = self.email_input.text().strip()
        password = self.pword_input.text().strip()
        pin = self.pin_input.text().strip()

        # Delegate validation and account creation to AuthService
        success, message = auth_service.create_account(
            username=username,
            name=name,
            email=email,
            password=password,
            pin=pin
        )

        if success:
            QMessageBox.information(self, "Success", "Account created successfully! You can now login.")
            self.accept()
        else:
            self.msg_label.setText(f"Error: {message}")


class LoginScreen(QWidget):
    login_successful = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurion - Login")
        self.setFixedSize(960, 600)
        self.setObjectName("aurionRoot")

        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ==========================================
        # LEFT PANEL: Brand Showcase
        # ==========================================
        left_panel = QFrame()
        left_panel.setStyleSheet("QFrame { background-color: #0d151e; border: none; }")
        left_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(48, 40, 48, 40)

        # Top Logo Header
        header_logo_layout = QHBoxLayout()
        header_logo_layout.setSpacing(12)
        header_logo_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        header_logo = QLabel()
        header_logo.setStyleSheet("border: none; background: transparent;")
        if os.path.exists(LOGO_PATH):
            header_logo.setPixmap(QPixmap(LOGO_PATH).scaled(
                26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))

        brand_text = QLabel("aurion")
        brand_text.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff; border: none; background: transparent;")

        header_logo_layout.addWidget(header_logo)
        header_logo_layout.addWidget(brand_text)
        header_logo_layout.addStretch()
        left_layout.addLayout(header_logo_layout)

        left_layout.addSpacing(32)

        # Hero Headlines
        left_eyebrow = QLabel("— EVERYDAY MONEY, REIMAGINED")
        left_eyebrow.setStyleSheet("color: #44e3c0; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        left_layout.addWidget(left_eyebrow)

        left_layout.addSpacing(8)

        hero_title = QLabel("A clearer way\nto move money.")
        hero_title.setStyleSheet("color: #ffffff; font-size: 34px; font-weight: 700; line-height: 1.25; border: none; background: transparent;")
        hero_title.setWordWrap(True)
        left_layout.addWidget(hero_title)

        left_layout.addSpacing(12)

        hero_sub = QLabel("Cash in, cash out, send, and pay. All from your Aurion account.")
        hero_sub.setStyleSheet("color: #94a3b8; font-size: 14px; line-height: 1.4; border: none; background: transparent;")
        hero_sub.setWordWrap(True)
        left_layout.addWidget(hero_sub)

        # Middle Circle Graphic (ID Scoped to prevent square border on child QLabel)
        center_wrapper = QHBoxLayout()
        center_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)

        graphic_container = QFrame()
        graphic_container.setObjectName("circleBadge")
        graphic_container.setFixedSize(180, 180)
        graphic_container.setStyleSheet("""
            QFrame#circleBadge {
                background-color: #0f1822;
                border: 1px solid #263544;
                border-radius: 90px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        graphic_layout = QHBoxLayout(graphic_container)
        graphic_layout.setContentsMargins(0, 0, 0, 0)
        graphic_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center_logo = QLabel()
        center_logo.setStyleSheet("border: none; background: transparent;")
        if os.path.exists(LOGO_PATH):
            center_logo.setPixmap(QPixmap(LOGO_PATH).scaled(
                105, 105, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))

        graphic_layout.addWidget(center_logo)
        center_wrapper.addWidget(graphic_container)
        left_layout.addLayout(center_wrapper, 1)

        # Footer Logo & Text
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        footer_logo = QLabel()
        footer_logo.setStyleSheet("border: none; background: transparent;")
        if os.path.exists(LOGO_PATH):
            footer_logo.setPixmap(QPixmap(LOGO_PATH).scaled(
                16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))

        footer_text = QLabel("Your money. Your direction.")
        footer_text.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500; border: none; background: transparent;")

        footer_layout.addWidget(footer_logo)
        footer_layout.addWidget(footer_text)
        footer_layout.addStretch()
        left_layout.addLayout(footer_layout)

        # ==========================================
        # RIGHT PANEL: Login Form
        # ==========================================
        right_panel = QFrame()
        right_panel.setStyleSheet("QFrame { background-color: #0b1118; border: none; }")
        right_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(60, 36, 60, 40)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        quit_btn = QPushButton("Quit  ✕")
        quit_btn.setProperty("aurionRole", "link")
        quit_btn.clicked.connect(QApplication.instance().quit)
        top_bar.addWidget(quit_btn)
        right_layout.addLayout(top_bar)

        right_layout.addStretch(1)

        right_eyebrow = QLabel("WELCOME TO AURION")
        right_eyebrow.setStyleSheet("color: #44e3c0; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        right_layout.addWidget(right_eyebrow)

        right_layout.addSpacing(4)

        welcome_title = QLabel("Welcome back.")
        welcome_title.setStyleSheet("color: #ffffff; font-size: 28px; font-weight: 700; border: none; background: transparent;")
        right_layout.addWidget(welcome_title)

        welcome_sub = QLabel("Log in to your personal account.")
        welcome_sub.setStyleSheet("color: #94a3b8; font-size: 14px; border: none; background: transparent;")
        right_layout.addWidget(welcome_sub)

        right_layout.addSpacing(24)

        lbl_user = QLabel("Username/Email")
        lbl_user.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        right_layout.addWidget(lbl_user)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username or email")
        right_layout.addWidget(self.username_input)

        right_layout.addSpacing(14)

        lbl_pass = QLabel("Password/PIN")
        lbl_pass.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        right_layout.addWidget(lbl_pass)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password or PIN")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        right_layout.addWidget(self.password_input)

        right_layout.addSpacing(24)

        self.login_btn = QPushButton("Login  →")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.clicked.connect(self.handle_login)
        right_layout.addWidget(self.login_btn)

        right_layout.addSpacing(20)

        divider_layout = QHBoxLayout()
        line_left = QFrame()
        line_left.setFrameShape(QFrame.Shape.HLine)
        line_left.setStyleSheet("background-color: #263544; max-height: 1px; border: none;")

        div_text = QLabel(" New to Aurion? ")
        div_text.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500; border: none; background: transparent;")

        line_right = QFrame()
        line_right.setFrameShape(QFrame.Shape.HLine)
        line_right.setStyleSheet("background-color: #263544; max-height: 1px; border: none;")

        divider_layout.addWidget(line_left, 1)
        divider_layout.addWidget(div_text)
        divider_layout.addWidget(line_right, 1)
        right_layout.addLayout(divider_layout)

        right_layout.addSpacing(16)

        self.signup_btn = QPushButton("Sign Up")
        self.signup_btn.clicked.connect(self.open_signup)
        right_layout.addWidget(self.signup_btn)

        right_layout.addStretch(1)

        root_layout.addWidget(left_panel, 1)
        root_layout.addWidget(right_panel, 1)

    def open_signup(self):
        signup_dialog = SignUpDialog(self)
        signup_dialog.exec()

    def handle_login(self):
        identifier = self.username_input.text().strip()
        secret = self.password_input.text().strip()

        # Delegate authentication to AuthService
        success, canonical_username, error_message = auth_service.login(identifier, secret)

        if success:
            self.login_successful.emit(canonical_username)
        else:
            QMessageBox.critical(self, "Login Failed", error_message)

