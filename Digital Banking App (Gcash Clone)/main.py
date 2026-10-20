import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.theme import apply_aurion_theme
from ui.login import LoginScreen
from ui.dashboard import DashboardScreen

# Suppress harmless Qt D-Bus portal warning on Linux
os.environ["QT_LOGGING_RULES"] = "qt.qpa.services=false"


class AurionApp:
    def __init__(self):
        # 1. MUST instantiate QApplication FIRST
        self.app = QApplication(sys.argv)

        # 2. Apply theme (sets Fusion style, QSS, and window icon)
        apply_aurion_theme(self.app)

        # 3. Initialize screens
        self.login_ui = LoginScreen()
        self.dashboard_ui = DashboardScreen()

        # Wire Qt signals
        self.login_ui.login_successful.connect(self.show_dashboard)
        self.dashboard_ui.logout_requested.connect(self.show_login)

    def show_dashboard(self, username):
        self.login_ui.hide()
        if hasattr(self.dashboard_ui, 'open_dashboard'):
            self.dashboard_ui.open_dashboard(username)
        else:
            self.dashboard_ui.show()

    def show_login(self):
        self.dashboard_ui.hide()
        self.login_ui.show()

    def run(self):
        self.login_ui.show()
        sys.exit(self.app.exec())


if __name__ == '__main__':
    aurion = AurionApp()
    aurion.run()