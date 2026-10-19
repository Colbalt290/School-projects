import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QDialog, QFormLayout, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from .theme import ICONS_DIR, LOGO_PATH
from core import bank_service


class ActionCard(QFrame):
    """Clickable action card for 'Move your money' section."""
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

        # Top icon row
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

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700; border: none; background: transparent;")
        layout.addWidget(title_label)

        # Subtitle
        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet("color: #647588; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(sub_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ReceiptDialog(QDialog):
    """Pop-up modal displaying full receipt details upon transaction completion."""
    def __init__(self, receipt_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aurion - Transaction Receipt")
        self.setFixedSize(360, 320)
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

        if os.path.exists(LOGO_PATH):
            self.setWindowIcon(QIcon(LOGO_PATH))

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

        # 1. Dashboard (Active)
        self.nav_dash = QPushButton("  Dashboard")
        self.nav_dash.setStyleSheet("""
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
        nav_items_layout.addWidget(self.nav_dash)

        # Helper to create nav action buttons
        def make_nav_btn(text, icon_name, on_click=None):
            btn = QPushButton(f"  {text}")
            icon_p = os.path.join(ICONS_DIR, icon_name)
            if os.path.exists(icon_p):
                btn.setIcon(QIcon(icon_p))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #8c9ba8;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    text-align: left;
                    padding: 9px 14px;
                }
                QPushButton:hover {
                    background-color: #0f1822;
                    color: #ffffff;
                }
            """)
            if on_click:
                btn.clicked.connect(on_click)
            return btn

        self.nav_cashin = make_nav_btn("Cash In", "cashin.png", self.handle_cash_in)
        self.nav_cashout = make_nav_btn("Cash Out", "cashout.png", self.handle_cash_out)
        self.nav_send = make_nav_btn("Send", "send.png", self.handle_send)
        self.nav_payment = make_nav_btn("Payment", "payment.png", self.handle_payment)

        nav_items_layout.addWidget(self.nav_cashin)
        nav_items_layout.addWidget(self.nav_cashout)
        nav_items_layout.addWidget(self.nav_send)
        nav_items_layout.addWidget(self.nav_payment)
        sidebar_layout.addLayout(nav_items_layout)

        sidebar_layout.addStretch(1)

        # Bottom: Logout Button
        self.logout_btn = QPushButton("  Log out")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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
        self.logout_btn.clicked.connect(self.handle_logout)
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
        # MAIN CONTENT AREA
        # ==========================================
        main_content = QFrame()
        main_content.setStyleSheet("background-color: #080e14; border: none;")
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(36, 20, 36, 24)
        content_layout.setSpacing(0)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        breadcrumb = QLabel("Aurion  <span style='color:#3a4a5b;'>/</span>  <span style='color:#94a3b8;'>Dashboard</span>")
        breadcrumb.setTextFormat(Qt.TextFormat.RichText)
        breadcrumb.setStyleSheet("color: #506173; font-size: 13px; font-weight: 500; border: none; background: transparent;")
        top_bar.addWidget(breadcrumb)

        top_bar.addStretch()

        # Header Profile Chip
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
        content_layout.addSpacing(24)

        # Scroll area for main dashboard body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #080e14;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #1b2938;
                border-radius: 3px;
                min-height: 20px;
            }
        """)

        body_widget = QWidget()
        body_widget.setStyleSheet("background-color: transparent;")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(20)

        # Greeting Title & Subtitle
        self.welcome_title = QLabel("Welcome back, User.")
        self.welcome_title.setStyleSheet("color: #ffffff; font-size: 28px; font-weight: 700; border: none; background: transparent;")
        body_layout.addWidget(self.welcome_title)

        welcome_sub = QLabel("Your money, at a glance.")
        welcome_sub.setStyleSheet("color: #8c9ba8; font-size: 13px; border: none; background: transparent;")
        body_layout.addWidget(welcome_sub)

        body_layout.addSpacing(4)

        # ==========================================
        # HERO BALANCE CARD
        # ==========================================
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

        # Left Info Column
        hero_left = QVBoxLayout()
        hero_left.setContentsMargins(0, 0, 0, 0)
        hero_left.setSpacing(6)

        # Balance Title & Eye toggle
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
        self.eye_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #142230;
            }
        """)
        self.eye_btn.clicked.connect(self.toggle_balance_visibility)
        bal_header_layout.addWidget(self.eye_btn)
        bal_header_layout.addStretch()

        hero_left.addLayout(bal_header_layout)

        # Large Balance Value
        self.balance_label = QLabel("PHP  0.00")
        self.balance_label.setStyleSheet("color: #ffffff; font-size: 38px; font-weight: 700; border: none; background: transparent;")
        hero_left.addWidget(self.balance_label)

        hero_left.addStretch()

        # Footer dot + account info
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

        # Right glowing illustration with Aurion logo centered on top
        art_container = QFrame()
        art_container.setStyleSheet("border: none; background: transparent;")
        art_container.setFixedSize(160, 142)
        art_layout = QGridLayout(art_container)
        art_layout.setContentsMargins(0, 0, 0, 0)

        glow_path = os.path.join(ICONS_DIR, "glow.png")
        if os.path.exists(glow_path):
            glow_label = QLabel()
            glow_label.setStyleSheet("border: none; background: transparent;")
            glow_label.setPixmap(QPixmap(glow_path).scaled(
                160, 142, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
            glow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            art_layout.addWidget(glow_label, 0, 0, Qt.AlignmentFlag.AlignCenter)

        logo_path = os.path.join(ICONS_DIR, "logo.png")
        if os.path.exists(logo_path):
            logo_art_label = QLabel()
            logo_art_label.setStyleSheet("border: none; background: transparent;")
            logo_art_label.setPixmap(QPixmap(logo_path).scaled(
                54, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
            logo_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            art_layout.addWidget(logo_art_label, 0, 0, Qt.AlignmentFlag.AlignCenter)

        hero_layout.addWidget(art_container, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        body_layout.addWidget(hero_card)

        # ==========================================
        # "MOVE YOUR MONEY" SECTION
        # ==========================================
        move_title = QLabel("Move your money")
        move_title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 700; border: none; background: transparent;")
        body_layout.addWidget(move_title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        card_cashin = ActionCard("Cash In", "Add to your balance", "cashin.png")
        card_cashin.clicked.connect(self.handle_cash_in)

        card_cashout = ActionCard("Cash Out", "Withdraw your funds", "cashout.png")
        card_cashout.clicked.connect(self.handle_cash_out)

        card_send = ActionCard("Send", "Send to an Aurion user", "send.png")
        card_send.clicked.connect(self.handle_send)

        card_payment = ActionCard("Payment", "Pay a biller or merchant", "payment.png")
        card_payment.clicked.connect(self.handle_payment)

        cards_layout.addWidget(card_cashin)
        cards_layout.addWidget(card_cashout)
        cards_layout.addWidget(card_send)
        cards_layout.addWidget(card_payment)

        body_layout.addLayout(cards_layout)

        # ==========================================
        # INBOX SECTION
        # ==========================================
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

        # Inbox Cards Container
        self.inbox_container = QVBoxLayout()
        self.inbox_container.setSpacing(10)
        body_layout.addLayout(self.inbox_container)

        scroll.setWidget(body_widget)
        content_layout.addWidget(scroll)

        root_layout.addWidget(main_content, 1)

    # ==========================================
    # Logic & Event Handlers
    # ==========================================
    def open_dashboard(self, username):
        self.current_user = username
        self.actual_balance = bank_service.get_balance(username)

        # Update labels & avatar initials
        initial = username[0].upper() if username else "U"
        self.sidebar_avatar.setText(initial)
        self.top_avatar.setText(initial)
        self.sidebar_username.setText(username)
        self.top_username.setText(username)
        self.welcome_title.setText(f"Welcome back, {username}.")

        self.update_balance_display()
        self.refresh_inbox()
        self.show()

    def toggle_balance_visibility(self):
        self.balance_hidden = not self.balance_hidden
        self.update_balance_display()

    def update_balance_display(self):
        eye_path = os.path.join(ICONS_DIR, "eye.png")
        has_eye_icon = os.path.exists(eye_path)

        if self.balance_hidden:
            self.balance_label.setText("PHP  • • • • • •")
            if has_eye_icon:
                self.eye_btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        background: transparent;
                        padding: 2px;
                        border-radius: 4px;
                        opacity: 0.35;
                    }
                    QPushButton:hover {
                        background-color: #142230;
                    }
                """)
            else:
                self.eye_btn.setText("👁‍🗨")
        else:
            self.balance_label.setText(f"PHP  {self.actual_balance:,.2f}")
            if has_eye_icon:
                self.eye_btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        background: transparent;
                        padding: 2px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #142230;
                    }
                """)
            else:
                self.eye_btn.setText("👁")

    def refresh_inbox(self):
        # Clear existing inbox item widgets
        while self.inbox_container.count():
            child = self.inbox_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        messages = bank_service.get_inbox(self.current_user)
        unread_count = len(messages)
        self.unread_badge.setText(f"{unread_count} unread" if unread_count > 0 else "0 unread")

        if not messages:
            empty_card = QFrame()
            empty_card.setStyleSheet("""
                QFrame {
                    background-color: #0e1722;
                    border: 1px solid #1b2938;
                    border-radius: 12px;
                    padding: 16px;
                }
            """)
            empty_layout = QHBoxLayout(empty_card)
            empty_msg = QLabel("No notifications yet.")
            empty_msg.setStyleSheet("color: #647588; font-size: 13px; border: none; background: transparent;")
            empty_layout.addWidget(empty_msg)
            self.inbox_container.addWidget(empty_card)
            return

        for msg in messages:
            item_card = QFrame()
            item_card.setStyleSheet("""
                QFrame {
                    background-color: #0e1722;
                    border: 1px solid #1b2938;
                    border-radius: 12px;
                }
                QFrame:hover {
                    background-color: #121e2c;
                    border: 1px solid #283e52;
                }
            """)
            item_layout = QHBoxLayout(item_card)
            item_layout.setContentsMargins(16, 14, 16, 14)
            item_layout.setSpacing(14)

            # Left badge with inbox icon
            icon_badge = QLabel()
            icon_badge.setFixedSize(36, 36)
            icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_badge.setStyleSheet("""
                background-color: #0f2b24;
                border: 1px solid #1c4b40;
                border-radius: 10px;
            """)
            inbox_icon_p = os.path.join(ICONS_DIR, "inbox.png")
            if os.path.exists(inbox_icon_p):
                icon_badge.setPixmap(QPixmap(inbox_icon_p).scaled(
                    18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                ))
            item_layout.addWidget(icon_badge)

            # Middle content text
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
    # Action Dialog Handlers
    # ==========================================
    def _create_action_dialog(self, title, input_placeholder):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Aurion - {title}")
        dialog.setFixedSize(340, 200)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b1118;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #0f1822;
                color: #f2f7fa;
                border: 1px solid #263544;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #44e3c0;
            }
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                font-weight: 700;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #70edce;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel(title.upper())
        header.setStyleSheet("color: #44e3c0; font-weight: 800; font-size: 14px; letter-spacing: 1px;")
        layout.addWidget(header)

        inp = QLineEdit()
        inp.setPlaceholderText(input_placeholder)
        layout.addWidget(inp)

        btn = QPushButton(f"Confirm {title}")
        layout.addWidget(btn)

        return dialog, inp, btn

    def handle_cash_in(self):
        dialog, amt_in, btn = self._create_action_dialog("Cash In", "Enter amount (PHP)")

        def run():
            try:
                amt = float(amt_in.text().strip())
                ok, new_bal_or_err, receipt = bank_service.cash_in(self.current_user, amt)
                if ok:
                    self.actual_balance = float(new_bal_or_err)
                    self.update_balance_display()
                    self.refresh_inbox()
                    dialog.accept()
                    self.show_receipt(receipt)
                else:
                    QMessageBox.warning(dialog, "Error", str(new_bal_or_err))
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Please enter a valid numeric amount.")

        btn.clicked.connect(run)
        dialog.exec()

    def handle_cash_out(self):
        dialog, amt_in, btn = self._create_action_dialog("Cash Out", "Enter amount (PHP)")
        btn.setText("Generate Cash-Out Code")

        def run():
            try:
                amt = float(amt_in.text().strip())
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Please enter a valid numeric amount.")
                return

            ok, code, exp_time, new_bal = bank_service.generate_cashout_code(self.current_user, amt)
            if ok:
                self.actual_balance = float(new_bal)
                self.update_balance_display()
                self.refresh_inbox()
                dialog.accept()
                self.show_cashout_code(code, amt, exp_time)
            else:
                QMessageBox.warning(dialog, "Error", str(code))

        btn.clicked.connect(run)
        dialog.exec()

    def show_cashout_code(self, code, amount, exp_time):
        dialog = QDialog(self)
        dialog.setWindowTitle("Aurion - Cash Out Reference Code")
        dialog.setFixedSize(340, 240)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b1118;
            }
            QLabel {
                color: #cbd5e1;
            }
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                font-weight: 700;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        info_label = QLabel(f"Present this reference code at any Aurion Kiosk<br>to claim <b>PHP {amount:,.2f}</b>:")
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #94a3b8; font-size: 13px;")

        code_label = QLabel(str(code))
        code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code_label.setStyleSheet("""
            font-size: 28px; 
            font-weight: 800; 
            color: #44e3c0; 
            letter-spacing: 5px; 
            background: #0e2220; 
            border: 1px solid #1a453d;
            padding: 10px; 
            border-radius: 10px;
        """)

        exp_label = QLabel(f"Expires today at: <b>{exp_time}</b> (5 min validity)")
        exp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        exp_label.setStyleSheet("color: #647588; font-size: 11px;")

        close_btn = QPushButton("Done")
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(info_label)
        layout.addWidget(code_label)
        layout.addWidget(exp_label)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def handle_send(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Aurion - Send Money")
        dialog.setFixedSize(360, 260)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b1118;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #0f1822;
                color: #f2f7fa;
                border: 1px solid #263544;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #44e3c0;
            }
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                font-weight: 700;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #70edce;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("SEND MONEY")
        header.setStyleSheet("color: #44e3c0; font-weight: 800; font-size: 14px; letter-spacing: 1px;")
        layout.addWidget(header)

        rec_in = QLineEdit()
        rec_in.setPlaceholderText("Recipient Username")

        amt_in = QLineEdit()
        amt_in.setPlaceholderText("Amount (PHP)")

        btn = QPushButton("Confirm Transfer")

        layout.addWidget(rec_in)
        layout.addWidget(amt_in)
        layout.addWidget(btn)

        def run():
            try:
                rec = rec_in.text().strip()
                amt = float(amt_in.text().strip())
                ok, new_bal_or_err, receipt = bank_service.send_money(self.current_user, rec, amt)
                if ok:
                    self.actual_balance = float(new_bal_or_err)
                    self.update_balance_display()
                    self.refresh_inbox()
                    dialog.accept()
                    self.show_receipt(receipt)
                else:
                    QMessageBox.warning(dialog, "Error", str(new_bal_or_err))
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Please enter a valid numeric amount.")

        btn.clicked.connect(run)
        dialog.exec()

    def handle_payment(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Aurion - Payment")
        dialog.setFixedSize(360, 260)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b1118;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #0f1822;
                color: #f2f7fa;
                border: 1px solid #263544;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #44e3c0;
            }
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                font-weight: 700;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #70edce;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("PAY BILL OR MERCHANT")
        header.setStyleSheet("color: #44e3c0; font-weight: 800; font-size: 14px; letter-spacing: 1px;")
        layout.addWidget(header)

        biller_in = QLineEdit()
        biller_in.setPlaceholderText("Biller / Merchant Name")

        amt_in = QLineEdit()
        amt_in.setPlaceholderText("Amount (PHP)")

        btn = QPushButton("Confirm Payment")

        layout.addWidget(biller_in)
        layout.addWidget(amt_in)
        layout.addWidget(btn)

        def run():
            try:
                biller = biller_in.text().strip()
                amt = float(amt_in.text().strip())
                ok, new_bal_or_err, receipt = bank_service.pay_bill(self.current_user, biller, amt)
                if ok:
                    self.actual_balance = float(new_bal_or_err)
                    self.update_balance_display()
                    self.refresh_inbox()
                    dialog.accept()
                    self.show_receipt(receipt)
                else:
                    QMessageBox.warning(dialog, "Error", str(new_bal_or_err))
            except ValueError:
                QMessageBox.warning(dialog, "Error", "Please enter a valid numeric amount.")

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
