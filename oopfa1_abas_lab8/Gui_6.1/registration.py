import sys
from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtGui import QFont, QGuiApplication

class RegistrationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Window setup
        self.setWindowTitle("Account Registration System")
        window_width = 440
        window_height = 490

        # Requirement: Center the GUI on the screen
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

        # Requirement: In-window Program Title (other than Window Title)
        self.title_label = QLabel("ACCOUNT REGISTRATION", self)
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.resize(300, 35)
        
        # Center title horizontally
        title_x = (window_width - self.title_label.width()) // 2
        self.title_label.move(title_x, 20)

        # List of required fields
        self.field_names = [
            "First Name:",
            "Last Name:",
            "Username:",
            "Password:",
            "Email Address:",
            "Contact Number:"
        ]

        self.inputs = {}

        # Position computed automatically based on top component (self.title_label)
        top_y = self.title_label.y()
        top_height = self.title_label.height()
        
        start_y = top_y + top_height + 25  # Starting baseline Y position below top component
        row_height = 30
        row_spacing = 15

        label_x = 35
        label_width = 120
        field_x = label_x + label_width + 10
        field_width = 220

        # Absolute Positioning
        for i, name in enumerate(self.field_names):
            current_y = start_y + i * (row_height + row_spacing)

            # Left side label
            label = QLabel(name, self)
            label.setFont(QFont("Arial", 10))
            label.resize(label_width, row_height)
            label.move(label_x, current_y)

            # Right side text field
            line_edit = QLineEdit(self)
            line_edit.resize(field_width, row_height)
            line_edit.move(field_x, current_y)

            # Mask password input
            if "Password" in name:
                line_edit.setEchoMode(QLineEdit.EchoMode.Password)

            # Store dictionary reference for clear/submit operations
            clean_key = name.replace(":", "")
            self.inputs[clean_key] = line_edit

        # Requirement: Buttons at the bottom (Submit on left, Clear on right)
        last_field_y = start_y + (len(self.field_names) - 1) * (row_height + row_spacing)
        button_y = last_field_y + row_height + 30
        button_width = 110
        button_height = 35

        # Submit button (Left)
        self.submit_btn = QPushButton("Submit", self)
        self.submit_btn.resize(button_width, button_height)
        self.submit_btn.move(label_x + 25, button_y)
        self.submit_btn.clicked.connect(self.submit_form)

        # Clear button (Right)
        self.clear_btn = QPushButton("Clear", self)
        self.clear_btn.resize(button_width, button_height)
        self.clear_btn.move(field_x + field_width - button_width - 25, button_y)
        self.clear_btn.clicked.connect(self.clear_fields)

        self.show()

    def clear_fields(self):
        """Clears all text inputs."""
        for field in self.inputs.values():
            field.clear()

    def submit_form(self):
        """Validates inputs and displays a success popup."""
        for name, field in self.inputs.items():
            if not field.text().strip():
                QMessageBox.warning(self, "Validation Error", f"Please fill out the '{name}' field.")
                field.setFocus()
                return

        QMessageBox.information(self, "Success", "Account Registration Successful!")
        self.clear_fields()