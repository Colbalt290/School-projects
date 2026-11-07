import sys
import math
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLineEdit, 
    QPushButton, QGridLayout, QVBoxLayout, QMessageBox, QFileDialog
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

class ScientificCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.history_file = "calculator_history.txt"
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Scientific Calculator")
        self.setGeometry(300, 300, 350, 420)

        # Central widget setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Display screen
        self.display = QLineEdit(self)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setFixedHeight(50)
        self.display.setReadOnly(True)
        display_font = self.display.font()
        display_font.setPointSize(16)
        self.display.setFont(display_font)
        main_layout.addWidget(self.display)

        # Button keypad layout
        grid = QGridLayout()
        main_layout.addLayout(grid)

        buttons = [
            ('sin', 0, 0), ('cos', 0, 1), ('^', 0, 2), ('C', 0, 3),
            ('7', 1, 0),   ('8', 1, 1),   ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0),   ('5', 2, 1),   ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0),   ('2', 3, 1),   ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0),   ('.', 4, 1),   ('=', 4, 2), ('+', 4, 3)
        ]

        for text, row, col in buttons:
            button = QPushButton(text)
            button.setFixedHeight(45)
            btn_font = button.font()
            btn_font.setPointSize(12)
            button.setFont(btn_font)
            button.clicked.connect(self.on_button_click)
            grid.addWidget(button, row, col)

        # Create top menu bar
        self.create_menu_bar()
        self.show()

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")

        save_action = QAction("Save History", self)
        save_action.triggered.connect(self.save_history)
        file_menu.addAction(save_action)

        retrieve_action = QAction("Retrieve History", self)
        retrieve_action.triggered.connect(self.retrieve_history)
        file_menu.addAction(retrieve_action)

        file_menu.addSeparator()

        # Exit action with Ctrl+Q shortcut
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit/Clear Menu
        edit_menu = menu_bar.addMenu("Edit")
        clear_action = QAction("Clear Display", self)
        clear_action.triggered.connect(self.clear_display)
        edit_menu.addAction(clear_action)

    def on_button_click(self):
        sender = self.sender()
        text = sender.text()

        if text == 'C':
            self.clear_display()
        elif text == '=':
            self.calculate_result()
        elif text in ('sin', 'cos'):
            self.calculate_trig(text)
        else:
            self.display.setText(self.display.text() + text)

    def clear_display(self):
        self.display.clear()

    def calculate_trig(self, func_name):
        expression = self.display.text().strip()
        if not expression:
            return
        try:
            val = float(eval(expression.replace('^', '**')))
            rad_val = math.radians(val)
            result = math.sin(rad_val) if func_name == 'sin' else math.cos(rad_val)
            result = round(result, 8)
            
            record = f"{func_name}({val}°) = {result}"
            self.display.setText(str(result))
            self.auto_save_record(record)
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid input for trig function.")

    def calculate_result(self):
        expression = self.display.text().strip()
        if not expression:
            return
        try:
            py_expression = expression.replace('^', '**')
            result = eval(py_expression)
            
            record = f"{expression} = {result}"
            self.display.setText(str(result))
            self.auto_save_record(record)
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid math expression.")

    def auto_save_record(self, record):
        """Appends each completed calculation to history file automatically."""
        try:
            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(record + "\n")
        except Exception as e:
            print("Failed to save record:", e)

    def save_history(self):
        """Export history file via QFileDialog."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export History", "calculator_history.txt", "Text Files (*.txt)")
        if file_path and os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as src:
                content = src.read()
            with open(file_path, "w", encoding="utf-8") as dest:
                dest.write(content)
            QMessageBox.information(self, "Saved", "Calculator history exported successfully!")

    def retrieve_history(self):
        """Open and display history file contents in a dialog."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open History File", "", "Text Files (*.txt)")
        target_path = file_path if file_path else self.history_file

        if os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content:
                QMessageBox.information(self, "Stored Operations History", content)
            else:
                QMessageBox.information(self, "History", "History file is empty.")
        else:
            QMessageBox.information(self, "History", "No history file found.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = ScientificCalculator()
    sys.exit(app.exec())