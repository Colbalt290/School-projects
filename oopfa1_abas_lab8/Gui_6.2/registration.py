import sys
import csv
import os
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

        # Center the GUI on the screen
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

        # In-window Program Title
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

        # Absolute Positioning calculated based on top title label
        top_y = self.title_label.y()
        top_height = self.title_label.height()
        
        start_y = top_y + top_height + 25  # Starting baseline Y position
        row_height = 30
        row_spacing = 15

        label_x = 35
        label_width = 120
        field_x = label_x + label_width + 10
        field_width = 220

        # Build form components
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

            clean_key = name.replace(":", "")
            self.inputs[clean_key] = line_edit

        # Buttons at bottom
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

    def save_to_csv(self, account_data):
        """Saves registered user data to a CSV file."""
        file_name = "registered_accounts.csv"
        file_exists = os.path.exists(file_name)

        with open(file_name, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(account_data.keys()))
            if not file_exists:
                writer.writeheader()  # Create CSV column headers if file is new
            writer.writerow(account_data)

    def submit_form(self):
        """Validates fields, saves registration data, and shows message boxes with standard symbols."""
        empty_fields = []

        # 1. Validation check for missing/empty values
        for name, field in self.inputs.items():
            if not field.text().strip():
                empty_fields.append(name)

        if empty_fields:
            missing_str = ", ".join(empty_fields)
            # Uses QMessageBox.warning symbol
            QMessageBox.warning(
                self, 
                "Missing Information", 
                f"Registration failed. Please complete the following required field(s):\n• {missing_str}"
            )
            return

        # 2. Collect field data
        account_data = {name: field.text().strip() for name, field in self.inputs.items()}

        # 3. Save to database/file
        try:
            self.save_to_csv(account_data)
            # Uses QMessageBox.information symbol
            QMessageBox.information(
                self, 
                "Registration Successful", 
                "Account registered and saved successfully to the database!"
            )
            self.clear_fields()
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Database Error", 
                f"An error occurred while saving the account:\n{str(e)}"
            )