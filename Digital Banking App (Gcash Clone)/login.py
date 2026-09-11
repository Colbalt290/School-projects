import PySimpleGUI as sg
from auth import auth
from db import bank_db

class LoginScreen:
    def __init__(self):
        sg.theme('DarkTeal9')
        sg.set_options(font=('Segoe UI', 11))

    # This is the signup block
    def open_signup(self):
        """Opens an account registration."""
        layout = [
            [sg.Text("Create Your Aurion Account", font=('Segoe UI', 14, 'bold'))],
            [sg.Text("Full Name:", size=(12, 1)), sg.Input(key='-NAME-')],
            [sg.Text("Username:", size=(12, 1)), sg.Input(key='-UN-')],
            [sg.Text("Email:", size=(12, 1)), sg.Input(key='-EMAIL-')],
            [sg.Text("Password:", size=(12, 1)), sg.Input(key='-PWORD-', password_char='*')],
            [sg.Text("4-Digit PIN:", size=(12, 1)), sg.Input(key='-PIN-', password_char='*')],
            [sg.Text("", size=(40, 1), key='-MSG-')],
            [sg.Button('Register', border_width=0), sg.Button('Cancel', border_width=0)]
        ]

        signup_window = sg.Window('Sign Up', layout, margins=(20,20))

        while True:
            event, values = signup_window.read() #Stereotypical block for closing a window
            if event in (sg.WINDOW_CLOSED, 'Cancel'):
                break

            if event == 'Register':
                if not all([values['-NAME-'], values['-UN-'], values['-EMAIL-'], values['-PWORD-'], values['-PIN-']]):
                    signup_window['-MSG-'].update("Error: All fields are required.", text_color="red")
                else:
                    success = bank_db.create_account(
                        values['-UN-'],
                        values['-NAME-'],
                        values['-EMAIL-'],
                        values['-PWORD-'],
                        values['-PIN-']
                    )
                    if success:
                        sg.popup("Account created successfully! You can now login.")
                        break
                    else:
                        signup_window['-MSG-'].update("Error: Username already exists.")
        signup_window.close()

    def open_login(self):
        layout = [
            [sg.Text("Welcome to Aurion!", font=('Segoe UI', 14, 'bold'))],
            [sg.Text("Username/Email:"), sg.Input(key='-UN-')],
            [sg.Text("Password/PIN:"), sg.Input(key='-PWORD-', password_char='*')],
            [sg.Text("", key='-OUTPUT-')],
            [sg.Button('Login'), sg.Button('Sign Up'), sg.Button('Quit')]
        ]

        window = sg.Window('Aurion Login', layout, margins=(20,20))

        while True:
            event, values = window.read()
            if event in (sg.WINDOW_CLOSED, 'Quit'):
                window.close()
                return None
                
            if event == 'Sign Up':
                window.hide()
                self.open_signup()
                window.un_hide()
                
            if event == 'Login':
                user = auth.verify_login(values['-UN-'], values['-PWORD-'])
                if user:
                    window.close()
                    return user
                window['-OUTPUT-'].update("Invalid credentials.", text_color="red")