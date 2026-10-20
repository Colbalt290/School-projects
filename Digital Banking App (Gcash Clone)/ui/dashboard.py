import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QFormLayout, QFrame, QScrollArea, QGridLayout,
    QStackedWidget, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from .theme import ICONS_DIR, LOGO_PATH, APP_ICON_PATH
from core import bank_service


class ActionCard(QFrame):
    """Clickable action card on Dashboard home for 'Move your money' section."""
    clicked = pyqtSignal()

    def __init__(self, title, subtitle, icon_name, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("actionCard")
        self.setStyleSheet("""
            QFrame#actionCard {
                background-color: #0e1722;
                border: 1px solid #1b2938;
                border-radius: 12px;
                padding: 14px;
            }
            QFrame#actionCard:hover {
                background-color: #13202e;
                border: 1px solid #2a4156;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel()
        icon_path = os.path.join(ICONS_DIR, icon_name)
        if os.path.exists(icon_path):
            icon_label.setPixmap(QPixmap(icon_path).scaled(
                22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        top_row.addWidget(icon_label)
        top_row.addStretch()

        arrow_label = QLabel()
        arrow_path = os.path.join(ICONS_DIR, "arrow.png")
        if os.path.exists(arrow_path):
            arrow_label.setPixmap(QPixmap(arrow_path).scaled(
                12, 12, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        else:
            arrow_label.setText("↗")
            arrow_label.setStyleSheet("color: #506173; font-size: 12px;")
        top_row.addWidget(arrow_label)

        layout.addLayout(top_row)
        layout.addSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700; border: none; background: transparent;")
        layout.addWidget(title_label)

        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet("color: #647588; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(sub_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class SideBalanceCard(QFrame):
    """Reusable 'Your balance' card shown on transaction pages."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self.setStyleSheet("""
            QFrame {
                background-color: #0e1722;
                border: 1px solid #1b2938;
                border-radius: 16px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(8)

        # Header with Logo
        head_row = QHBoxLayout()
        lbl_head = QLabel("Your balance")
        lbl_head.setStyleSheet("color: #8c9ba8; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        head_row.addWidget(lbl_head)
        head_row.addStretch()

        logo_label = QLabel()
        if os.path.exists(LOGO_PATH):
            logo_label.setPixmap(QPixmap(LOGO_PATH).scaled(
                22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        head_row.addWidget(logo_label)
        layout.addLayout(head_row)

        layout.addSpacing(4)

        lbl_php = QLabel("PHP")
        lbl_php.setStyleSheet("color: #8c9ba8; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        layout.addWidget(lbl_php)

        self.bal_amount = QLabel("0.00")
        self.bal_amount.setStyleSheet("color: #ffffff; font-size: 32px; font-weight: 800; border: none; background: transparent;")
        layout.addWidget(self.bal_amount)

        layout.addSpacing(6)

        # Divider line
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #1b2938; max-height: 1px; border: none;")
        layout.addWidget(div)

        layout.addSpacing(4)

        self.lbl_user = QLabel("User")
        self.lbl_user.setStyleSheet("color: #8c9ba8; font-size: 13px; border: none; background: transparent;")
        layout.addWidget(self.lbl_user)

    def set_data(self, balance, username):
        self.bal_amount.setText(f"{balance:,.2f}")
        self.lbl_user.setText(username)


class AmountInputBox(QFrame):
    """Custom styled input box with integrated 'PHP' currency prefix."""
    def __init__(self, placeholder="Enter amount", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0f1822;
                border: 1px solid #263544;
                border-radius: 8px;
            }
            QFrame:focus-within {
                border: 1px solid #44e3c0;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        prefix = QLabel("PHP")
        prefix.setStyleSheet("color: #44e3c0; font-size: 13px; font-weight: 700; border: none; background: transparent;")
        layout.addWidget(prefix)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f2f7fa;
                font-size: 14px;
                padding: 8px 0;
            }
        """)
        layout.addWidget(self.input, 1)

    def text(self):
        return self.input.text()

    def clear(self):
        self.input.clear()


class CashOutCodeDialog(QDialog):
    """Modern Cash Out Reference Code popup matching Figma design."""
    def __init__(self, code, amount, exp_time, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aurion - Cash Out Reference Code")
        self.setFixedSize(400, 420)
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        self.setStyleSheet("""
            QDialog {
                background-color: #0d151e;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Top icon badge (green square with up-right arrow)
        badge = QLabel()
        badge.setFixedSize(44, 44)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            background-color: #0f2c24;
            border: 1px solid #1a483e;
            border-radius: 10px;
        """)
        arrow_p = os.path.join(ICONS_DIR, "cashout.png")
        if os.path.exists(arrow_p):
            badge.setPixmap(QPixmap(arrow_p).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(badge)

        title = QLabel("Cash Out Reference Code")
        title.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 700;")
        layout.addWidget(title)

        sub = QLabel(f"Present this code at any Aurion Kiosk to claim <b style='color:#ffffff;'>PHP {amount:,.2f}</b>.")
        sub.setTextFormat(Qt.TextFormat.RichText)
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #8c9ba8; font-size: 13px; line-height: 1.4;")
        layout.addWidget(sub)

        # Code Container Box
        code_box = QFrame()
        code_box.setStyleSheet("""
            QFrame {
                background-color: #070e16;
                border: 1px solid #1c2b3a;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        code_box_layout = QVBoxLayout(code_box)
        code_box_layout.setContentsMargins(14, 16, 14, 16)
        code_box_layout.setSpacing(6)

        ref_lbl = QLabel("Reference number")
        ref_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ref_lbl.setStyleSheet("color: #8c9ba8; font-size: 12px; background: transparent; border: none;")
        code_box_layout.addWidget(ref_lbl)

        code_text = QLabel(str(code))
        code_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code_text.setStyleSheet("color: #44e3c0; font-size: 42px; font-weight: 800; letter-spacing: 6px; background: transparent; border: none;")
        code_box_layout.addWidget(code_text)

        layout.addWidget(code_box)

        # Expiry clock row
        exp_row = QHBoxLayout()
        exp_row.setSpacing(8)
        exp_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        clock_icon = QLabel()
        clock_p = os.path.join(ICONS_DIR, "clock.png")
        if os.path.exists(clock_p):
            clock_icon.setPixmap(QPixmap(clock_p).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        exp_row.addWidget(clock_icon)

        exp_lbl = QLabel(f"Expires today at <b style='color:#ffffff;'>{exp_time}</b><br><span style='color:#627588;'>5-minute validity</span>")
        exp_lbl.setTextFormat(Qt.TextFormat.RichText)
        exp_lbl.setStyleSheet("color: #8c9ba8; font-size: 12px;")
        exp_row.addWidget(exp_lbl)
        exp_row.addStretch()

        layout.addLayout(exp_row)
        layout.addStretch()

        # Done button
        done_btn = QPushButton("Done")
        done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        done_btn.setFixedHeight(44)
        done_btn.setStyleSheet("""
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                font-size: 14px;
                font-weight: 700;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #70edce;
            }
        """)
        done_btn.clicked.connect(self.accept)
        layout.addWidget(done_btn)


class ReceiptDialog(QDialog):
    """Pop-up modal displaying full receipt details upon transaction completion."""
    def __init__(self, receipt_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aurion - Transaction Receipt")
        self.setFixedSize(360, 320)
        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        self.setStyleSheet("""
            QDialog {
                background-color: #0b1118;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 13px;
            }
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                font-weight: 700;
                border-radius: 8px;
                padding: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #70edce;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("TRANSACTION RECEIPT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: 800; font-size: 15px; color: #44e3c0; letter-spacing: 1px;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        def make_val(text, is_amount=False):
            lbl = QLabel(text)
            if is_amount:
                lbl.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 14px;")
            else:
                lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
            return lbl

        form.addRow("Type:", make_val(str(receipt_data.get("type", ""))))
        form.addRow("Recipient:", make_val(str(receipt_data.get("recipient", ""))))
        form.addRow("Amount:", make_val(f"PHP {receipt_data.get('amount', 0.0):,.2f}", is_amount=True))
        form.addRow("Timestamp:", make_val(str(receipt_data.get("timestamp", ""))))
        form.addRow("Txn ID:", make_val(str(receipt_data.get("trans_num", ""))))
        form.addRow("Ref No:", make_val(str(receipt_data.get("ref_num", ""))))
        layout.addLayout(form)

        layout.addStretch()

        close_btn = QPushButton("Done")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class DashboardScreen(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurion - Dashboard")
        self.setFixedSize(1120, 720)
        self.current_user = None
        self.balance_hidden = False
        self.actual_balance = 0.0

        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ==========================================
        # LEFT SIDEBAR
        # ==========================================
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #080e14;
                border-right: 1px solid #14202c;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 24, 20, 24)
        sidebar_layout.setSpacing(0)

        # Brand header
        brand_layout = QHBoxLayout()
        brand_layout.setSpacing(10)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        brand_logo = QLabel()
        brand_logo.setStyleSheet("border: none; background: transparent;")
        if os.path.exists(LOGO_PATH):
            brand_logo.setPixmap(QPixmap(LOGO_PATH).scaled(
                24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))

        brand_name = QLabel("aurion")
        brand_name.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 700; border: none; background: transparent;")

        brand_layout.addWidget(brand_logo)
        brand_layout.addWidget(brand_name)
        brand_layout.addStretch()
        sidebar_layout.addLayout(brand_layout)

        sidebar_layout.addSpacing(32)

        # Section label
        workspace_label = QLabel("WORKSPACE")
        workspace_label.setStyleSheet("color: #506173; font-size: 11px; font-weight: 700; letter-spacing: 1px; border: none; background: transparent;")
        sidebar_layout.addWidget(workspace_label)

        sidebar_layout.addSpacing(12)

        # Navigation menu items
        nav_items_layout = QVBoxLayout()
        nav_items_layout.setSpacing(6)

        def create_nav_btn(text, icon_name, page_idx):
            btn = QPushButton(f"  {text}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            icon_p = os.path.join(ICONS_DIR, icon_name)
            if os.path.exists(icon_p):
                btn.setIcon(QIcon(icon_p))
            btn.clicked.connect(lambda: self.switch_page(page_idx))
            return btn

        self.nav_dash = create_nav_btn("Dashboard", "logo.png", 0)
        self.nav_cashin = create_nav_btn("Cash In", "cashin.png", 1)
        self.nav_cashout = create_nav_btn("Cash Out", "cashout.png", 2)
        self.nav_send = create_nav_btn("Send", "send.png", 3)
        self.nav_payment = create_nav_btn("Payment", "payment.png", 4)

        self.nav_buttons = [
            self.nav_dash,
            self.nav_cashin,
            self.nav_cashout,
            self.nav_send,
            self.nav_payment,
        ]

        for b in self.nav_buttons:
            nav_items_layout.addWidget(b)

        sidebar_layout.addLayout(nav_items_layout)
        sidebar_layout.addStretch(1)

        # Bottom: Logout Button
        self.logout_btn = QPushButton("  Log out")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_p = os.path.join(ICONS_DIR, "arrow.png")
        if os.path.exists(logout_p):
            self.logout_btn.setIcon(QIcon(logout_p))
        self.logout_btn.clicked.connect(lambda: self.switch_page(5))
        sidebar_layout.addWidget(self.logout_btn)

        sidebar_layout.addSpacing(12)

        # Bottom: User Profile Card
        user_card = QFrame()
        user_card.setStyleSheet("background-color: transparent; border: none;")
        user_card_layout = QHBoxLayout(user_card)
        user_card_layout.setContentsMargins(6, 6, 6, 6)
        user_card_layout.setSpacing(10)

        self.sidebar_avatar = QLabel("C")
        self.sidebar_avatar.setFixedSize(34, 34)
        self.sidebar_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar_avatar.setStyleSheet("""
            background-color: #0e2e28;
            color: #44e3c0;
            border: 1px solid #1a4d42;
            border-radius: 17px;
            font-size: 14px;
            font-weight: 700;
        """)

        user_text_layout = QVBoxLayout()
        user_text_layout.setContentsMargins(0, 0, 0, 0)
        user_text_layout.setSpacing(2)

        self.sidebar_username = QLabel("User")
        self.sidebar_username.setStyleSheet("color: #f1f5f9; font-size: 13px; font-weight: 600; border: none; background: transparent;")

        sidebar_sub = QLabel("Personal account")
        sidebar_sub.setStyleSheet("color: #627588; font-size: 11px; border: none; background: transparent;")

        user_text_layout.addWidget(self.sidebar_username)
        user_text_layout.addWidget(sidebar_sub)

        user_card_layout.addWidget(self.sidebar_avatar)
        user_card_layout.addLayout(user_text_layout)
        sidebar_layout.addWidget(user_card)

        root_layout.addWidget(sidebar)

        # ==========================================
        # MAIN CONTENT AREA (STACKED WIDGET)
        # ==========================================
        main_content = QFrame()
        main_content.setStyleSheet("background-color: #080e14; border: none;")
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(36, 20, 36, 24)
        content_layout.setSpacing(0)

        # Top Bar (Breadcrumbs & Profile Chip)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        self.breadcrumb = QLabel("Aurion  <span style='color:#3a4a5b;'>/</span>  <span style='color:#94a3b8;'>Dashboard</span>")
        self.breadcrumb.setTextFormat(Qt.TextFormat.RichText)
        self.breadcrumb.setStyleSheet("color: #506173; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        top_bar.addWidget(self.breadcrumb)

        top_bar.addStretch()

        top_profile = QFrame()
        top_profile.setStyleSheet("border: none; background: transparent;")
        top_profile_layout = QHBoxLayout(top_profile)
        top_profile_layout.setContentsMargins(0, 0, 0, 0)
        top_profile_layout.setSpacing(10)

        self.top_username = QLabel("User")
        self.top_username.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600; border: none; background: transparent;")

        self.top_avatar = QLabel("C")
        self.top_avatar.setFixedSize(28, 28)
        self.top_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top_avatar.setStyleSheet("""
            background-color: #0e2e28;
            color: #44e3c0;
            border: 1px solid #1a4d42;
            border-radius: 14px;
            font-size: 12px;
            font-weight: 700;
        """)

        top_profile_layout.addWidget(self.top_username)
        top_profile_layout.addWidget(self.top_avatar)
        top_bar.addWidget(top_profile)

        content_layout.addLayout(top_bar)
        content_layout.addSpacing(20)

        # Stacked Pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        # Page 0: Dashboard Home
        self.page_dash = self._build_dashboard_page()
        self.stack.addWidget(self.page_dash)

        # Page 1: Cash In Page
        self.page_cashin = self._build_cashin_page()
        self.stack.addWidget(self.page_cashin)

        # Page 2: Cash Out Page
        self.page_cashout = self._build_cashout_page()
        self.stack.addWidget(self.page_cashout)

        # Page 3: Send Money Page
        self.page_send = self._build_send_page()
        self.stack.addWidget(self.page_send)

        # Page 4: Payment Page
        self.page_payment = self._build_payment_page()
        self.stack.addWidget(self.page_payment)

        # Page 5: Logout Page
        self.page_logout = self._build_logout_page()
        self.stack.addWidget(self.page_logout)

        content_layout.addWidget(self.stack, 1)
        root_layout.addWidget(main_content, 1)

        self.switch_page(0)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)

        # Page titles for breadcrumb
        titles = ["Dashboard", "Cash In", "Cash Out", "Send Money", "Payment", "Log out"]
        current_title = titles[index] if index < len(titles) else "Dashboard"
        self.breadcrumb.setText(f"Aurion  <span style='color:#3a4a5b;'>/</span>  <span style='color:#94a3b8;'>{current_title}</span>")

        # Update sidebar active styling
        for idx, btn in enumerate(self.nav_buttons):
            if idx == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0f2622;
                        color: #44e3c0;
                        border: 1px solid #1b453d;
                        border-radius: 8px;
                        font-size: 13px;
                        font-weight: 700;
                        text-align: left;
                        padding: 10px 14px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #8c9ba8;
                        border: none;
                        border-radius: 8px;
                        font-size: 13px;
                        font-weight: 500;
                        text-align: left;
                        padding: 10px 14px;
                    }
                    QPushButton:hover {
                        background-color: #0f1822;
                        color: #ffffff;
                    }
                """)

        if index == 5:
            self.logout_btn.setStyleSheet("""
                QPushButton {
                    background-color: #172230;
                    color: #ffffff;
                    border: 1px solid #283e54;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 700;
                    text-align: left;
                    padding: 10px 14px;
                }
            """)
        else:
            self.logout_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #8c9ba8;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    text-align: left;
                    padding: 10px 14px;
                }
                QPushButton:hover {
                    background-color: #1a151b;
                    color: #ff6b6b;
                }
            """)

    # ==========================================
    # BUILD PAGES
    # ==========================================
    def _build_dashboard_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical { border: none; background: #080e14; width: 6px; margin: 0; }
            QScrollBar::handle:vertical { background: #1b2938; border-radius: 3px; min-height: 20px; }
        """)

        body_widget = QWidget()
        body_widget.setStyleSheet("background-color: transparent;")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(20)

        # Greeting Title
        self.welcome_title = QLabel("Welcome back, User.")
        self.welcome_title.setStyleSheet("color: #ffffff; font-size: 28px; font-weight: 700; border: none; background: transparent;")
        body_layout.addWidget(self.welcome_title)

        welcome_sub = QLabel("Your money, at a glance.")
        welcome_sub.setStyleSheet("color: #8c9ba8; font-size: 13px; border: none; background: transparent;")
        body_layout.addWidget(welcome_sub)
        body_layout.addSpacing(4)

        # Hero Balance Card
        hero_card = QFrame()
        hero_card.setFixedHeight(190)
        hero_card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0d1722, stop:1 #111d2a);
                border: 1px solid #1b2938;
                border-radius: 16px;
            }
        """)
        hero_layout = QHBoxLayout(hero_card)
        hero_layout.setContentsMargins(32, 20, 32, 20)

        hero_left = QVBoxLayout()
        hero_left.setContentsMargins(0, 0, 0, 0)
        hero_left.setSpacing(6)

        bal_header_layout = QHBoxLayout()
        bal_header_layout.setSpacing(8)
        bal_header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        avail_label = QLabel("Available balance")
        avail_label.setStyleSheet("color: #8c9ba8; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        bal_header_layout.addWidget(avail_label)

        self.eye_btn = QPushButton()
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_btn.setFixedSize(22, 22)
        eye_path = os.path.join(ICONS_DIR, "eye.png")
        if os.path.exists(eye_path):
            self.eye_btn.setIcon(QIcon(eye_path))
            self.eye_btn.setIconSize(QSize(16, 16))
        else:
            self.eye_btn.setText("👁")
        self.eye_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding: 2px; }")
        self.eye_btn.clicked.connect(self.toggle_balance_visibility)
        bal_header_layout.addWidget(self.eye_btn)
        bal_header_layout.addStretch()
        hero_left.addLayout(bal_header_layout)

        self.balance_label = QLabel("PHP  0.00")
        self.balance_label.setStyleSheet("color: #ffffff; font-size: 38px; font-weight: 700; border: none; background: transparent;")
        hero_left.addWidget(self.balance_label)
        hero_left.addStretch()

        hero_foot_layout = QHBoxLayout()
        hero_foot_layout.setSpacing(8)
        hero_foot_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        dot_label = QLabel("●")
        dot_label.setStyleSheet("color: #22c55e; font-size: 10px; border: none; background: transparent;")
        account_desc = QLabel("Personal account  <span style='color:#3a4a5b;'>/</span>  Philippine peso")
        account_desc.setTextFormat(Qt.TextFormat.RichText)
        account_desc.setStyleSheet("color: #5e7082; font-size: 12px; border: none; background: transparent;")
        hero_foot_layout.addWidget(dot_label)
        hero_foot_layout.addWidget(account_desc)
        hero_foot_layout.addStretch()

        hero_left.addLayout(hero_foot_layout)
        hero_layout.addLayout(hero_left, 1)

        # Right glowing illustration with Aurion logo centered
        art_container = QFrame()
        art_container.setStyleSheet("border: none; background: transparent;")
        art_container.setFixedSize(160, 142)
        art_layout = QGridLayout(art_container)
        art_layout.setContentsMargins(0, 0, 0, 0)

        glow_path = os.path.join(ICONS_DIR, "glow.png")
        if os.path.exists(glow_path):
            glow_label = QLabel()
            glow_label.setStyleSheet("border: none; background: transparent;")
            glow_label.setPixmap(QPixmap(glow_path).scaled(160, 142, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            glow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            art_layout.addWidget(glow_label, 0, 0, Qt.AlignmentFlag.AlignCenter)

        if os.path.exists(LOGO_PATH):
            logo_art_label = QLabel()
            logo_art_label.setStyleSheet("border: none; background: transparent;")
            logo_art_label.setPixmap(QPixmap(LOGO_PATH).scaled(54, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            logo_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            art_layout.addWidget(logo_art_label, 0, 0, Qt.AlignmentFlag.AlignCenter)

        hero_layout.addWidget(art_container, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        body_layout.addWidget(hero_card)

        # "Move your money" Section
        move_title = QLabel("Move your money")
        move_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700; border: none; background: transparent;")
        body_layout.addWidget(move_title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        card_cashin = ActionCard("Cash In", "Add to your balance", "cashin.png")
        card_cashin.clicked.connect(lambda: self.switch_page(1))

        card_cashout = ActionCard("Cash Out", "Withdraw your funds", "cashout.png")
        card_cashout.clicked.connect(lambda: self.switch_page(2))

        card_send = ActionCard("Send", "Send to an Aurion user", "send.png")
        card_send.clicked.connect(lambda: self.switch_page(3))

        card_payment = ActionCard("Payment", "Pay a biller or merchant", "payment.png")
        card_payment.clicked.connect(lambda: self.switch_page(4))

        cards_layout.addWidget(card_cashin)
        cards_layout.addWidget(card_cashout)
        cards_layout.addWidget(card_send)
        cards_layout.addWidget(card_payment)
        body_layout.addLayout(cards_layout)

        # Inbox Section
        inbox_header_layout = QHBoxLayout()
        inbox_header_layout.setSpacing(10)
        inbox_header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        inbox_title = QLabel("Inbox")
        inbox_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700; border: none; background: transparent;")
        inbox_header_layout.addWidget(inbox_title)

        self.unread_badge = QLabel("0 unread")
        self.unread_badge.setStyleSheet("""
            background-color: #0f2b24;
            color: #44e3c0;
            border: 1px solid #1a453b;
            border-radius: 9px;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
        """)
        inbox_header_layout.addWidget(self.unread_badge)
        inbox_header_layout.addStretch()
        body_layout.addLayout(inbox_header_layout)

        self.inbox_container = QVBoxLayout()
        self.inbox_container.setSpacing(10)
        body_layout.addLayout(self.inbox_container)

        scroll.setWidget(body_widget)
        return scroll

    def _build_transaction_frame(self, icon_name, title_text, fields_widget, confirm_hint, confirm_text, on_confirm):
        """Creates the standardized left transaction card matching Figma."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame#txnCard {
                background-color: #0e1722;
                border: 1px solid #1b2938;
                border-radius: 16px;
            }
        """)
        card.setObjectName("txnCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with green icon badge
        head_row = QHBoxLayout()
        head_row.setSpacing(12)
        head_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        badge = QLabel()
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("background-color: #0f2c24; border: 1px solid #1a483e; border-radius: 8px;")
        icon_p = os.path.join(ICONS_DIR, icon_name)
        if os.path.exists(icon_p):
            badge.setPixmap(QPixmap(icon_p).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        head_row.addWidget(badge)

        t_layout = QVBoxLayout()
        t_layout.setSpacing(2)
        lbl_t = QLabel("Transaction details")
        lbl_t.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700; border: none; background: transparent;")
        lbl_sub = QLabel("All fields are required")
        lbl_sub.setStyleSheet("color: #647588; font-size: 12px; border: none; background: transparent;")
        t_layout.addWidget(lbl_t)
        t_layout.addWidget(lbl_sub)
        head_row.addLayout(t_layout)
        head_row.addStretch()
        layout.addLayout(head_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #1b2938; max-height: 1px; border: none;")
        layout.addWidget(div)

        # Form fields
        layout.addWidget(fields_widget)

        # Checkmark note container
        note_box = QFrame()
        note_box.setStyleSheet("background-color: #0c151f; border: 1px solid #1a2938; border-radius: 8px;")
        note_layout = QHBoxLayout(note_box)
        note_layout.setContentsMargins(12, 10, 12, 10)
        note_layout.setSpacing(8)

        check_icon = QLabel("✓")
        check_icon.setStyleSheet("color: #44e3c0; font-size: 13px; font-weight: bold; border: none; background: transparent;")
        note_layout.addWidget(check_icon)

        note_lbl = QLabel(confirm_hint)
        note_lbl.setStyleSheet("color: #8c9ba8; font-size: 12px; border: none; background: transparent;")
        note_layout.addWidget(note_lbl, 1)
        layout.addWidget(note_box)

        layout.addSpacing(6)

        # Bottom buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(42)
        cancel_btn.setFixedWidth(100)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #14202e;
                color: #cbd5e1;
                border: 1px solid #243547;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #19283a;
                color: #ffffff;
            }
        """)
        cancel_btn.clicked.connect(lambda: self.switch_page(0))
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton(f"{confirm_text}  →")
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setFixedHeight(42)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #70edce;
            }
        """)
        confirm_btn.clicked.connect(on_confirm)
        btn_row.addWidget(confirm_btn, 1)

        layout.addLayout(btn_row)
        return card

    def _build_page_shell(self, title, subtitle, left_widget, info_text):
        """Reusable wrapper for transaction pages with right balance card & back button."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(18)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #ffffff; font-size: 28px; font-weight: 800; border: none; background: transparent;")
        container_layout.addWidget(lbl_title)

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #8c9ba8; font-size: 13px; border: none; background: transparent;")
        container_layout.addWidget(lbl_sub)

        container_layout.addSpacing(6)

        # Two columns: Form Card on left, Balance Card & info on right
        cols = QHBoxLayout()
        cols.setSpacing(24)
        cols.addWidget(left_widget, 1)

        # Right Column
        right_col = QVBoxLayout()
        right_col.setSpacing(14)
        right_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        bal_card = SideBalanceCard()
        self.side_balance_cards.append(bal_card)
        right_col.addWidget(bal_card)

        # Info Box below balance card
        info_row = QHBoxLayout()
        info_row.setSpacing(8)
        info_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        info_icon = QLabel()
        info_p = os.path.join(ICONS_DIR, "infoicon.png")
        if os.path.exists(info_p):
            info_icon.setPixmap(QPixmap(info_p).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            info_icon.setText("ⓘ")
            info_icon.setStyleSheet("color: #44e3c0; font-size: 14px;")
        info_row.addWidget(info_icon)

        info_lbl = QLabel(info_text)
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #8c9ba8; font-size: 12px; line-height: 1.35;")
        info_row.addWidget(info_lbl, 1)

        info_container = QWidget()
        info_container.setFixedWidth(280)
        info_container.setLayout(info_row)
        right_col.addWidget(info_container)

        cols.addLayout(right_col)
        container_layout.addLayout(cols)

        # Back to Dashboard Link
        container_layout.addSpacing(10)
        back_btn = QPushButton("←  Back to Dashboard")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #8c9ba8;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                padding: 4px 0;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        back_btn.clicked.connect(lambda: self.switch_page(0))
        container_layout.addWidget(back_btn)

        container_layout.addStretch()
        return container

    # --- Cash In Page (Image 3) ---
    def _build_cashin_page(self):
        self.side_balance_cards = []

        fields = QWidget()
        f_layout = QVBoxLayout(fields)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(8)

        lbl = QLabel("Amount (PHP)")
        lbl.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600;")
        f_layout.addWidget(lbl)

        self.cashin_input = AmountInputBox()
        f_layout.addWidget(self.cashin_input)

        card = self._build_transaction_frame(
            icon_name="cashin.png",
            title_text="Cash In",
            fields_widget=fields,
            confirm_hint="Check the amount before confirming your cash in.",
            confirm_text="Confirm Cash In",
            on_confirm=self.submit_cash_in
        )

        return self._build_page_shell(
            title="Cash In",
            subtitle="Add money to your Aurion account.",
            left_widget=card,
            info_text="Your cash in will add to your Aurion balance."
        )

    # --- Cash Out Page ---
    def _build_cashout_page(self):
        fields = QWidget()
        f_layout = QVBoxLayout(fields)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(8)

        lbl = QLabel("Amount (PHP)")
        lbl.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600;")
        f_layout.addWidget(lbl)

        self.cashout_input = AmountInputBox()
        f_layout.addWidget(self.cashout_input)

        card = self._build_transaction_frame(
            icon_name="cashout.png",
            title_text="Cash Out",
            fields_widget=fields,
            confirm_hint="A 6-digit code will be generated to claim cash at any kiosk.",
            confirm_text="Generate Cash-Out Code",
            on_confirm=self.submit_cash_out
        )

        return self._build_page_shell(
            title="Cash Out",
            subtitle="Withdraw funds via any Aurion Kiosk terminal.",
            left_widget=card,
            info_text="Present the generated 6-digit code at any Aurion Kiosk to dispense your cash."
        )

    # --- Send Money Page (Image 1) ---
    def _build_send_page(self):
        fields = QWidget()
        f_layout = QVBoxLayout(fields)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(8)

        lbl_rec = QLabel("Recipient username")
        lbl_rec.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600;")
        f_layout.addWidget(lbl_rec)

        self.send_rec_input = QLineEdit()
        self.send_rec_input.setPlaceholderText("Enter recipient username")
        self.send_rec_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f1822;
                border: 1px solid #263544;
                border-radius: 8px;
                color: #f2f7fa;
                font-size: 14px;
                padding: 10px 14px;
            }
            QLineEdit:focus { border: 1px solid #44e3c0; }
        """)
        f_layout.addWidget(self.send_rec_input)

        f_layout.addSpacing(6)

        lbl_amt = QLabel("Amount (PHP)")
        lbl_amt.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600;")
        f_layout.addWidget(lbl_amt)

        self.send_amt_input = AmountInputBox()
        f_layout.addWidget(self.send_amt_input)

        card = self._build_transaction_frame(
            icon_name="send.png",
            title_text="Send Money",
            fields_widget=fields,
            confirm_hint="Check the recipient username and amount before sending.",
            confirm_text="Confirm Send",
            on_confirm=self.submit_send_money
        )

        return self._build_page_shell(
            title="Send Money",
            subtitle="Send money to another Aurion user.",
            left_widget=card,
            info_text="Use the recipient's Aurion username to send money to their account."
        )

    # --- Payment Page (Image 2) ---
    def _build_payment_page(self):
        fields = QWidget()
        f_layout = QVBoxLayout(fields)
        f_layout.setContentsMargins(0, 0, 0, 0)
        f_layout.setSpacing(8)

        lbl_biller = QLabel("Biller / Merchant")
        lbl_biller.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600;")
        f_layout.addWidget(lbl_biller)

        self.payment_biller_input = QLineEdit()
        self.payment_biller_input.setPlaceholderText("Enter biller or merchant")
        self.payment_biller_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f1822;
                border: 1px solid #263544;
                border-radius: 8px;
                color: #f2f7fa;
                font-size: 14px;
                padding: 10px 14px;
            }
            QLineEdit:focus { border: 1px solid #44e3c0; }
        """)
        f_layout.addWidget(self.payment_biller_input)

        f_layout.addSpacing(6)

        lbl_amt = QLabel("Amount (PHP)")
        lbl_amt.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600;")
        f_layout.addWidget(lbl_amt)

        self.payment_amt_input = AmountInputBox()
        f_layout.addWidget(self.payment_amt_input)

        card = self._build_transaction_frame(
            icon_name="payment.png",
            title_text="Payment",
            fields_widget=fields,
            confirm_hint="Check the biller or merchant and amount before paying.",
            confirm_text="Confirm Payment",
            on_confirm=self.submit_payment
        )

        return self._build_page_shell(
            title="Payment",
            subtitle="Pay a biller or merchant from your Aurion account.",
            left_widget=card,
            info_text="Enter the biller or merchant you want to pay, then the amount in PHP."
        )

    # --- Logout Confirmation Page (Image 6) ---
    def _build_logout_page(self):
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 40, 0, 0)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QFrame#logoutCard {
                background-color: #0e1722;
                border: 1px solid #1b2938;
                border-radius: 16px;
                padding: 32px;
            }
        """)
        card.setObjectName("logoutCard")

        l_layout = QVBoxLayout(card)
        l_layout.setContentsMargins(28, 28, 28, 28)
        l_layout.setSpacing(16)
        l_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge = QLabel()
        badge.setFixedSize(50, 50)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("background-color: #0f2c24; border: 1px solid #1a483e; border-radius: 12px;")
        exit_p = os.path.join(ICONS_DIR, "arrow.png")
        if os.path.exists(exit_p):
            badge.setPixmap(QPixmap(exit_p).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        l_layout.addWidget(badge)

        t = QLabel("Ready to log out?")
        t.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 700;")
        l_layout.addWidget(t)

        sub = QLabel("Are you sure you want to log out?")
        sub.setStyleSheet("color: #8c9ba8; font-size: 13px;")
        l_layout.addWidget(sub)

        l_layout.addSpacing(6)

        # Signed in user card
        u_box = QFrame()
        u_box.setFixedHeight(54)
        u_box.setStyleSheet("background-color: #070e16; border: 1px solid #1b2838; border-radius: 10px;")
        u_box_layout = QHBoxLayout(u_box)
        u_box_layout.setContentsMargins(12, 8, 12, 8)
        u_box_layout.setSpacing(10)

        self.logout_avatar = QLabel("C")
        self.logout_avatar.setFixedSize(32, 32)
        self.logout_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logout_avatar.setStyleSheet("background-color: #0e2e28; color: #44e3c0; border: 1px solid #1a4d42; border-radius: 16px; font-weight: 700;")
        u_box_layout.addWidget(self.logout_avatar)

        u_info = QVBoxLayout()
        u_info.setSpacing(1)
        self.logout_username = QLabel("User")
        self.logout_username.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        lbl_sign = QLabel("Currently signed in")
        lbl_sign.setStyleSheet("color: #627588; font-size: 11px; border: none; background: transparent;")
        u_info.addWidget(self.logout_username)
        u_info.addWidget(lbl_sign)
        u_box_layout.addLayout(u_info)
        u_box_layout.addStretch()

        l_layout.addWidget(u_box)
        l_layout.addSpacing(8)

        # Yes log out button
        yes_btn = QPushButton("Yes, log out  →")
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setFixedHeight(44)
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                font-size: 14px;
                font-weight: 700;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #70edce; }
        """)
        yes_btn.clicked.connect(self.perform_logout)
        l_layout.addWidget(yes_btn)

        # No stay logged in button
        no_btn = QPushButton("No, stay logged in")
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setFixedHeight(44)
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #14202e;
                color: #cbd5e1;
                font-size: 14px;
                font-weight: 600;
                border: 1px solid #243547;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #19283a; color: #ffffff; }
        """)
        no_btn.clicked.connect(lambda: self.switch_page(0))
        l_layout.addWidget(no_btn)

        c_layout.addWidget(card)

        # Footer branding
        c_layout.addSpacing(24)
        foot = QHBoxLayout()
        foot.setSpacing(8)
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        foot_logo = QLabel()
        if os.path.exists(LOGO_PATH):
            foot_logo.setPixmap(QPixmap(LOGO_PATH).scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        foot_lbl = QLabel("Your money. Your direction.")
        foot_lbl.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500;")
        foot.addWidget(foot_logo)
        foot.addWidget(foot_lbl)
        c_layout.addLayout(foot)

        c_layout.addStretch()
        return container

    # ==========================================
    # Logic & State Handlers
    # ==========================================
    def open_dashboard(self, username):
        self.current_user = username
        self.actual_balance = bank_service.get_balance(username)

        initial = username[0].upper() if username else "U"
        self.sidebar_avatar.setText(initial)
        self.top_avatar.setText(initial)
        self.logout_avatar.setText(initial)

        self.sidebar_username.setText(username)
        self.top_username.setText(username)
        self.logout_username.setText(username)
        self.welcome_title.setText(f"Welcome back, {username}.")

        self.update_balance_display()
        self.refresh_inbox()
        self.switch_page(0)
        self.show()

    def toggle_balance_visibility(self):
        self.balance_hidden = not self.balance_hidden
        self.update_balance_display()

    def update_balance_display(self):
        eye_path = os.path.join(ICONS_DIR, "eye.png")
        has_eye = os.path.exists(eye_path)

        if self.balance_hidden:
            self.balance_label.setText("PHP  • • • • • •")
            if has_eye:
                self.eye_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding: 2px; opacity: 0.35; }")
            else:
                self.eye_btn.setText("👁‍🗨")
        else:
            self.balance_label.setText(f"PHP  {self.actual_balance:,.2f}")
            if has_eye:
                self.eye_btn.setStyleSheet("QPushButton { border: none; background: transparent; padding: 2px; }")
            else:
                self.eye_btn.setText("👁")

        # Update all side balance cards across pages
        for card in self.side_balance_cards:
            card.set_data(self.actual_balance, self.current_user)

    def refresh_inbox(self):
        while self.inbox_container.count():
            child = self.inbox_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        messages = bank_service.get_inbox(self.current_user)
        unread_count = len(messages)
        self.unread_badge.setText(f"{unread_count} unread" if unread_count > 0 else "0 unread")

        if not messages:
            empty_card = QFrame()
            empty_card.setStyleSheet("background-color: #0e1722; border: 1px solid #1b2938; border-radius: 12px; padding: 16px;")
            empty_layout = QHBoxLayout(empty_card)
            empty_msg = QLabel("No notifications yet.")
            empty_msg.setStyleSheet("color: #647588; font-size: 13px; border: none; background: transparent;")
            empty_layout.addWidget(empty_msg)
            self.inbox_container.addWidget(empty_card)
            return

        for msg in messages:
            item_card = QFrame()
            item_card.setStyleSheet("background-color: #0e1722; border: 1px solid #1b2938; border-radius: 12px;")
            item_layout = QHBoxLayout(item_card)
            item_layout.setContentsMargins(16, 14, 16, 14)
            item_layout.setSpacing(14)

            icon_badge = QLabel()
            icon_badge.setFixedSize(36, 36)
            icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_badge.setStyleSheet("background-color: #0f2b24; border: 1px solid #1c4b40; border-radius: 10px;")
            inbox_icon_p = os.path.join(ICONS_DIR, "inbox.png")
            if os.path.exists(inbox_icon_p):
                icon_badge.setPixmap(QPixmap(inbox_icon_p).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            item_layout.addWidget(icon_badge)

            text_layout = QVBoxLayout()
            text_layout.setContentsMargins(0, 0, 0, 0)
            text_layout.setSpacing(2)

            msg_title = QLabel("Account notification")
            msg_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600; border: none; background: transparent;")
            msg_body = QLabel(msg)
            msg_body.setWordWrap(True)
            msg_body.setStyleSheet("color: #8c9ba8; font-size: 12px; border: none; background: transparent;")

            text_layout.addWidget(msg_title)
            text_layout.addWidget(msg_body)
            item_layout.addLayout(text_layout, 1)

            self.inbox_container.addWidget(item_card)

    def show_receipt(self, receipt_data):
        receipt_dialog = ReceiptDialog(receipt_data, self)
        receipt_dialog.exec()

    # ==========================================
    # TRANSACTION SUBMISSION METHODS
    # ==========================================
    def submit_cash_in(self):
        try:
            amt = float(self.cashin_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric amount.")
            return

        ok, new_bal_or_err, receipt = bank_service.cash_in(self.current_user, amt)
        if ok:
            self.actual_balance = float(new_bal_or_err)
            self.cashin_input.clear()
            self.update_balance_display()
            self.refresh_inbox()
            self.show_receipt(receipt)
            self.switch_page(0)
        else:
            QMessageBox.warning(self, "Transaction Failed", str(new_bal_or_err))

    def submit_cash_out(self):
        try:
            amt = float(self.cashout_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric amount.")
            return

        ok, code, exp_time, new_bal = bank_service.generate_cashout_code(self.current_user, amt)
        if ok:
            self.actual_balance = float(new_bal)
            self.cashout_input.clear()
            self.update_balance_display()
            self.refresh_inbox()
            code_dialog = CashOutCodeDialog(code, amt, exp_time, self)
            code_dialog.exec()
            self.switch_page(0)
        else:
            QMessageBox.warning(self, "Transaction Failed", str(code))

    def submit_send_money(self):
        rec = self.send_rec_input.text().strip()
        if not rec:
            QMessageBox.warning(self, "Missing Recipient", "Please enter the recipient username.")
            return

        try:
            amt = float(self.send_amt_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid numeric amount.")
            return

        ok, new_bal_or_err, receipt = bank_service.send_money(self.current_user, rec, amt)
        if ok:
            self.actual_balance = float(new_bal_or_err)
            self.send_rec_input.clear()
            self.send_amt_input.clear()
            self.update_balance_display()
            self.refresh_inbox()
            self.show_receipt(receipt)
            self.switch_page(0)
        else:
            QMessageBox.warning(self, "Transfer Failed", str(new_bal_or_err))

    def submit_payment(self):
        biller = self.payment_biller_input.text().strip()
        if not biller:
            QMessageBox.warning(self, "Missing Biller", "Please enter the biller or merchant name.")
            return

        try:
            amt = float(self.payment_amt_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid numeric amount.")
            return

        ok, new_bal_or_err, receipt = bank_service.pay_bill(self.current_user, biller, amt)
        if ok:
            self.actual_balance = float(new_bal_or_err)
            self.payment_biller_input.clear()
            self.payment_amt_input.clear()
            self.update_balance_display()
            self.refresh_inbox()
            self.show_receipt(receipt)
            self.switch_page(0)
        else:
            QMessageBox.warning(self, "Payment Failed", str(new_bal_or_err))

    def perform_logout(self):
        self.hide()
        self.logout_requested.emit()
