import sys
from PyQt6.QtWidgets import QApplication
from login import LoginScreen
from dashboard import DashboardScreen

class AurionApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_ui = LoginScreen()
        self.dashboard_ui = DashboardScreen()

        # Wire Qt signals to handle screen transitions
        self.login_ui.login_successful.connect(self.show_dashboard)
        self.dashboard_ui.logout_requested.connect(self.show_login)

    def show_dashboard(self, username):
        self.login_ui.hide()
        self.dashboard_ui.open_dashboard(username)

    def show_login(self):
        self.dashboard_ui.hide()
        self.login_ui.show()

    def run(self):
        self.login_ui.show()
        sys.exit(self.app.exec())

if __name__ == '__main__':
    app = AurionApp()
    app.run()