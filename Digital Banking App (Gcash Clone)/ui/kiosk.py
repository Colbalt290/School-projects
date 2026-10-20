import sys
import os

# Ensure project root is in sys.path when running script directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QMessageBox, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from ui.theme import apply_aurion_theme, ICONS_DIR, LOGO_PATH, APP_ICON_PATH
from core import bank_service


class AurionKioskTerminal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurion - Kiosk Terminal #001")
        self.setFixedSize(1100, 700)

        if os.path.exists(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        self.setStyleSheet("background-color: #080e14;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 24, 40, 24)
        main_layout.setSpacing(16)

        # Buffer string for keypad entry
        self.current_code = ""
        self.last_receipt = None

        # ==========================================
        # 1. TOP HEADER BAR
        # ==========================================
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        brand_logo = QLabel()
        if os.path.exists(LOGO_PATH):
            brand_logo.setPixmap(QPixmap(LOGO_PATH).scaled(
                24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))
        top_bar.addWidget(brand_logo)
        top_bar.addSpacing(6)

        brand_text = QLabel("aurion")
        brand_text.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 800; border: none; background: transparent;")
        top_bar.addWidget(brand_text)

        kiosk_subtitle = QLabel("  |  Kiosk Terminal")
        kiosk_subtitle.setStyleSheet("color: #8c9ba8; font-size: 14px; font-weight: 500; border: none; background: transparent;")
        top_bar.addWidget(kiosk_subtitle)

        top_bar.addStretch()

        term_dot = QLabel("●")
        term_dot.setStyleSheet("color: #22c55e; font-size: 10px; border: none; background: transparent;")
        term_lbl = QLabel("Terminal #001")
        term_lbl.setStyleSheet("color: #8c9ba8; font-size: 13px; font-weight: 600; border: none; background: transparent;")

        top_bar.addWidget(term_dot)
        top_bar.addSpacing(6)
        top_bar.addWidget(term_lbl)

        main_layout.addLayout(top_bar)

        top_divider = QFrame()
        top_divider.setFrameShape(QFrame.Shape.HLine)
        top_divider.setStyleSheet("background-color: #14202c; max-height: 1px; border: none;")
        main_layout.addWidget(top_divider)

        # ==========================================
        # 2. STEPPER PROGRESS ROW
        # ==========================================
        stepper_layout = QHBoxLayout()
        stepper_layout.setContentsMargins(0, 8, 0, 8)
        stepper_layout.setSpacing(12)

        self.step1_pill = QLabel(" 1  Enter code ")
        self.step1_pill.setStyleSheet("""
            background-color: #0f2c24;
            color: #44e3c0;
            border: 1px solid #1a483e;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
        """)
        stepper_layout.addWidget(self.step1_pill)

        self.step_line = QFrame()
        self.step_line.setFixedWidth(40)
        self.step_line.setFixedHeight(2)
        self.step_line.setStyleSheet("background-color: #1b2938; border: none;")
        stepper_layout.addWidget(self.step_line)

        self.step2_pill = QLabel(" 2  Collect cash ")
        self.step2_pill.setStyleSheet("""
            background-color: transparent;
            color: #627588;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
        """)
        stepper_layout.addWidget(self.step2_pill)

        stepper_layout.addStretch()
        main_layout.addLayout(stepper_layout)

        # ==========================================
        # 3. CONTENT STACK (Step 1 & Step 2)
        # ==========================================
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        # Page 0: Step 1 (Keypad Code Entry)
        self.page_step1 = self._build_step1_widget()
        self.stack.addWidget(self.page_step1)

        # Page 1: Step 2 (Cash Dispensed & Receipt)
        self.page_step2 = self._build_step2_widget()
        self.stack.addWidget(self.page_step2)

        main_layout.addWidget(self.stack, 1)

        # ==========================================
        # 4. FOOTER BAR
        # ==========================================
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)

        shield_icon = QLabel()
        sec_p = os.path.join(ICONS_DIR, "securitylogo.png")
        if os.path.exists(sec_p):
            shield_icon.setPixmap(QPixmap(sec_p).scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        footer_layout.addWidget(shield_icon)
        footer_layout.addSpacing(6)

        sec_lbl = QLabel("Your security. Our priority.")
        sec_lbl.setStyleSheet("color: #647588; font-size: 12px; border: none; background: transparent;")
        footer_layout.addWidget(sec_lbl)

        footer_layout.addStretch()

        made_simple = QLabel("Banking, made simple.")
        made_simple.setStyleSheet("color: #647588; font-size: 12px; border: none; background: transparent;")
        footer_layout.addWidget(made_simple)

        main_layout.addLayout(footer_layout)

    # ==========================================
    # STEP 1 WIDGET (Image 5)
    # ==========================================
    def _build_step1_widget(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(48)

        # Left Column: Welcome & Info
        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        left_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        badge = QLabel()
        badge.setFixedSize(44, 44)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("background-color: #0f2c24; border: 1px solid #1a483e; border-radius: 10px;")
        atm_p = os.path.join(ICONS_DIR, "cashout.png")
        if os.path.exists(atm_p):
            badge.setPixmap(QPixmap(atm_p).scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        left_col.addWidget(badge)

        title = QLabel("Welcome to your\nAurion Kiosk.")
        title.setStyleSheet("color: #ffffff; font-size: 34px; font-weight: 800; line-height: 1.25; border: none; background: transparent;")
        left_col.addWidget(title)

        sub = QLabel("Enter your six-digit cash out code to collect\nyour money.")
        sub.setStyleSheet("color: #8c9ba8; font-size: 14px; line-height: 1.4; border: none; background: transparent;")
        left_col.addWidget(sub)

        left_col.addSpacing(8)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #1b2938; max-height: 1px; border: none;")
        left_col.addWidget(div)

        left_col.addSpacing(8)

        # Note with info icon
        note_row = QHBoxLayout()
        note_row.setSpacing(12)
        note_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        info_icon = QLabel()
        info_p = os.path.join(ICONS_DIR, "infoicon.png")
        if os.path.exists(info_p):
            info_icon.setPixmap(QPixmap(info_p).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            info_icon.setText("📱")
        note_row.addWidget(info_icon)

        note_text_layout = QVBoxLayout()
        note_text_layout.setSpacing(2)
        lbl_h = QLabel("Use the code from your cash out")
        lbl_h.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        lbl_b = QLabel("You'll find it in your Aurion cash out confirmation. Keep your code private.")
        lbl_b.setWordWrap(True)
        lbl_b.setStyleSheet("color: #647588; font-size: 12px; border: none; background: transparent;")
        note_text_layout.addWidget(lbl_h)
        note_text_layout.addWidget(lbl_b)
        note_row.addLayout(note_text_layout, 1)

        left_col.addLayout(note_row)
        layout.addLayout(left_col, 1)

        # Right Column: ATM Keypad Card
        card = QFrame()
        card.setFixedWidth(440)
        card.setStyleSheet("""
            QFrame#keypadCard {
                background-color: #0e1722;
                border: 1px solid #1b2938;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        card.setObjectName("keypadCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        # Header row
        code_header = QHBoxLayout()
        lbl_title = QLabel("Cash out code")
        lbl_title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700; border: none; background: transparent;")
        self.code_count_lbl = QLabel("0 / 6 digits")
        self.code_count_lbl.setStyleSheet("color: #8c9ba8; font-size: 12px; border: none; background: transparent;")
        code_header.addWidget(lbl_title)
        code_header.addStretch()
        code_header.addWidget(self.code_count_lbl)
        card_layout.addLayout(code_header)

        # 6 Digital Code Boxes
        boxes_layout = QHBoxLayout()
        boxes_layout.setSpacing(8)
        self.digit_boxes = []

        for i in range(6):
            box = QLabel("")
            box.setFixedSize(52, 58)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setStyleSheet("""
                background-color: #080f17;
                border: 1px solid #1c2b3a;
                border-radius: 8px;
                color: #44e3c0;
                font-size: 26px;
                font-weight: 800;
            """)
            boxes_layout.addWidget(box)
            self.digit_boxes.append(box)

        card_layout.addLayout(boxes_layout)
        card_layout.addSpacing(6)

        # Keypad Grid (3x4)
        keypad = QGridLayout()
        keypad.setSpacing(10)

        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('Clear', 3, 0), ('0', 3, 1), ('Dispense  →', 3, 2)
        ]

        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(50)

            if text == 'Clear':
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #14202e;
                        color: #cbd5e1;
                        border: 1px solid #203144;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: 600;
                    }
                    QPushButton:hover { background-color: #1a2a3c; color: #ffffff; }
                """)
                btn.clicked.connect(self.handle_clear)
            elif 'Dispense' in text:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #44e3c0;
                        color: #07251f;
                        border: none;
                        border-radius: 8px;
                        font-size: 14px;
                        font-weight: 800;
                    }
                    QPushButton:hover { background-color: #70edce; }
                """)
                btn.clicked.connect(self.handle_dispense)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #14202e;
                        color: #ffffff;
                        border: 1px solid #203144;
                        border-radius: 8px;
                        font-size: 18px;
                        font-weight: 700;
                    }
                    QPushButton:hover { background-color: #1a2c3e; border: 1px solid #2a4058; }
                """)
                btn.clicked.connect(lambda _, d=text: self.handle_num_click(d))

            keypad.addWidget(btn, row, col)

        card_layout.addLayout(keypad)
        layout.addWidget(card)

        return container

    # ==========================================
    # STEP 2 WIDGET (Image 7 - Cash Dispensed)
    # ==========================================
    def _build_step2_widget(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(48)

        # Left Column: Success message
        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        left_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        check_circle = QLabel("✓")
        check_circle.setFixedSize(48, 48)
        check_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_circle.setStyleSheet("""
            background-color: #0f2c24;
            color: #44e3c0;
            border: 1px solid #1a483e;
            border-radius: 24px;
            font-size: 22px;
            font-weight: 800;
        """)
        left_col.addWidget(check_circle)

        title = QLabel("Cash Dispensed")
        title.setStyleSheet("color: #ffffff; font-size: 34px; font-weight: 800; border: none; background: transparent;")
        left_col.addWidget(title)

        sub = QLabel("Your money is ready. Please take your cash\nfrom the dispenser below.")
        sub.setStyleSheet("color: #8c9ba8; font-size: 14px; line-height: 1.4; border: none; background: transparent;")
        left_col.addWidget(sub)

        left_col.addSpacing(8)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #1b2938; max-height: 1px; border: none;")
        left_col.addWidget(div)

        left_col.addSpacing(8)

        # Note: Before you leave
        note_row = QHBoxLayout()
        note_row.setSpacing(12)
        note_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        info_icon = QLabel()
        info_p = os.path.join(ICONS_DIR, "infoicon.png")
        if os.path.exists(info_p):
            info_icon.setPixmap(QPixmap(info_p).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            info_icon.setText("📄")
        note_row.addWidget(info_icon)

        note_text_layout = QVBoxLayout()
        note_text_layout.setSpacing(2)
        lbl_h = QLabel("Before you leave")
        lbl_h.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        lbl_b = QLabel("Collect your cash and receipt. Keep the reference number for your records.")
        lbl_b.setWordWrap(True)
        lbl_b.setStyleSheet("color: #647588; font-size: 12px; border: none; background: transparent;")
        note_text_layout.addWidget(lbl_h)
        note_text_layout.addWidget(lbl_b)
        note_row.addLayout(note_text_layout, 1)

        left_col.addLayout(note_row)
        layout.addLayout(left_col, 1)

        # Right Column: Kiosk Receipt Card
        card = QFrame()
        card.setFixedWidth(440)
        card.setStyleSheet("""
            QFrame#receiptCard {
                background-color: #0e1722;
                border: 1px solid #1b2938;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        card.setObjectName("receiptCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        # Top row: Kiosk Receipt & Completed badge
        head_row = QHBoxLayout()
        r_title = QLabel("Kiosk Receipt")
        r_title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 700; border: none; background: transparent;")
        head_row.addWidget(r_title)
        head_row.addStretch()

        comp_badge = QLabel("✓ Completed")
        comp_badge.setStyleSheet("""
            background-color: #0f2c24;
            color: #44e3c0;
            border: 1px solid #1a483e;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 10px;
        """)
        head_row.addWidget(comp_badge)
        card_layout.addLayout(head_row)

        # Amount Dispensed Box
        amt_box = QFrame()
        amt_box.setStyleSheet("background-color: #080f17; border: 1px solid #1c2b3a; border-radius: 10px;")
        amt_box_layout = QVBoxLayout(amt_box)
        amt_box_layout.setContentsMargins(16, 12, 16, 12)
        amt_box_layout.setSpacing(4)

        amt_sub = QLabel("Amount Dispensed")
        amt_sub.setStyleSheet("color: #8c9ba8; font-size: 12px; border: none; background: transparent;")
        amt_box_layout.addWidget(amt_sub)

        self.step2_amount = QLabel("PHP  0.00")
        self.step2_amount.setStyleSheet("color: #ffffff; font-size: 32px; font-weight: 800; border: none; background: transparent;")
        amt_box_layout.addWidget(self.step2_amount)
        card_layout.addWidget(amt_box)

        # Receipt Key-Value Rows
        form = QVBoxLayout()
        form.setSpacing(10)

        def make_row(label, val_widget):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #8c9ba8; font-size: 13px; border: none; background: transparent;")
            row.addWidget(lbl)
            row.addStretch()
            val_widget.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 500; border: none; background: transparent;")
            row.addWidget(val_widget)
            return row

        self.r_terminal = QLabel("Aurion Kiosk #001")
        self.r_user = QLabel("User")
        self.r_timestamp = QLabel("2026-10-20 00:00")
        self.r_ref = QLabel("AR-000000000")

        form.addLayout(make_row("Terminal", self.r_terminal))
        form.addLayout(make_row("Account User", self.r_user))
        form.addLayout(make_row("Timestamp", self.r_timestamp))
        form.addLayout(make_row("Ref Number", self.r_ref))

        card_layout.addLayout(form)
        card_layout.addStretch()

        # Finish / Collect Receipt Button
        finish_btn = QPushButton("Take Cash / Collect Receipt  ↓")
        finish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        finish_btn.setFixedHeight(48)
        finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #44e3c0;
                color: #07251f;
                font-size: 14px;
                font-weight: 800;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #70edce; }
        """)
        finish_btn.clicked.connect(self.reset_to_step1)
        card_layout.addWidget(finish_btn)

        layout.addWidget(card)
        return container

    # ==========================================
    # KIOSK LOGIC HANDLERS
    # ==========================================
    def handle_num_click(self, digit):
        if len(self.current_code) < 6:
            self.current_code += digit
            self.update_display()

    def handle_clear(self):
        self.current_code = ""
        self.update_display()

    def update_display(self):
        count = len(self.current_code)
        self.code_count_lbl.setText(f"{count} / 6 digits")

        for i in range(6):
            if i < count:
                self.digit_boxes[i].setText(self.current_code[i])
                self.digit_boxes[i].setStyleSheet("""
                    background-color: #080f17;
                    border: 1px solid #44e3c0;
                    border-radius: 8px;
                    color: #44e3c0;
                    font-size: 26px;
                    font-weight: 800;
                """)
            else:
                self.digit_boxes[i].setText("")
                self.digit_boxes[i].setStyleSheet("""
                    background-color: #080f17;
                    border: 1px solid #1c2b3a;
                    border-radius: 8px;
                    color: #44e3c0;
                    font-size: 26px;
                    font-weight: 800;
                """)

    def handle_dispense(self):
        if len(self.current_code) != 6:
            QMessageBox.warning(self, "Incomplete Code", "Please enter a full 6-digit reference code.")
            return

        success, message, receipt = bank_service.redeem_cashout_code(self.current_code)

        if success:
            self.last_receipt = receipt
            self.show_step2(receipt)
        else:
            QMessageBox.critical(self, "Redemption Failed", message)
            self.handle_clear()

    def show_step2(self, receipt):
        # Update stepper header
        self.step1_pill.setStyleSheet("""
            background-color: #0f2c24;
            color: #44e3c0;
            border: 1px solid #1a483e;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
        """)
        self.step_line.setStyleSheet("background-color: #44e3c0; border: none;")
        self.step2_pill.setStyleSheet("""
            background-color: #0f2c24;
            color: #44e3c0;
            border: 1px solid #1a483e;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
        """)

        # Populate receipt card
        amt = receipt.get("amount", 0.0)
        self.step2_amount.setText(f"PHP  {amt:,.2f}")
        self.r_terminal.setText("Aurion Kiosk #001")
        self.r_user.setText(str(receipt.get("recipient", "")))
        self.r_timestamp.setText(str(receipt.get("timestamp", "")))
        self.r_ref.setText(str(receipt.get("ref_num", "")))

        self.stack.setCurrentIndex(1)

    def reset_to_step1(self):
        self.current_code = ""
        self.update_display()

        # Reset stepper header
        self.step1_pill.setStyleSheet("""
            background-color: #0f2c24;
            color: #44e3c0;
            border: 1px solid #1a483e;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
        """)
        self.step_line.setStyleSheet("background-color: #1b2938; border: none;")
        self.step2_pill.setStyleSheet("""
            background-color: transparent;
            color: #627588;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
        """)

        self.stack.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_aurion_theme(app)

    kiosk = AurionKioskTerminal()
    kiosk.show()
    sys.exit(app.exec())
