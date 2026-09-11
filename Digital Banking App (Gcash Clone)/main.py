from login import LoginScreen
from dashboard import DashboardScreen

class AurionApp:
    def __init__(self):
        # Instantiate your UI classes once when the app starts
        self.login_ui = LoginScreen()
        self.dashboard_ui = DashboardScreen()

    def run(self):
        # The main application loop
        while True:
            # Trigger the login screen method
            logged_in_user = self.login_ui.open_login()

            # If the user closed the window or hit Quit, end the program
            if logged_in_user is None:
                break

            # Open the dashboard for the authenticated user
            self.dashboard_ui.open_dashboard(logged_in_user)

if __name__ == '__main__':
    app = AurionApp()
    app.run()