import PySimpleGUI as sg
from auth import verify_login
from db import create_account
sg.theme('DarkTeal9')
sg.set_options(font=('Segoe UI', 11))


def open_login():
#Login window Layout
    layout = [
            [sg.Text("Welcome to Aurion's Digital Banking Service.", font=('Segoe UI', 14, 'bold'), pad=(0, 10))],
            [sg.Text("Username or Email:")],
            [sg.Input(key='-UN-')],
            [sg.Text("Password or PIN:")],
            [sg.Input(key='-PWORD-', password_char='*')],
            [sg.Text("", size=(40, 1), key='-OUTPUT-')],
            [sg.Button('Login', border_width=0), sg.Button('Sign Up', border_width=0), sg.Button('Quit', border_width=0)]
            ]

#Create the window
    window = sg.Window('Aurion Banking Service', layout, margins=(20,20))

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, 'Quit'):
            window.close()
            return None

        if event == 'Sign Up':
            window.hide()
            open_signup()
            window.un_hide()    

        if event == 'Login':
            entered_id = values['-UN-']
            entered_secret = values['-PWORD-']
            active_user = verify_login(entered_id, entered_secret)

            if active_user is not None:
                window.close()
                return active_user
            else:
                window['-OUTPUT-'].update("Error: Invalid credentials.", text_color = "red")

def open_signup():
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
        event, values = signup_window.read()
        if event in (sg.WINDOW_CLOSED, 'Cancel'):
            break

        if event == 'Register':

            if not all([values['-NAME-'], values['-UN-'], values['-EMAIL-'], values['-PWORD-'], values['-PIN-']]):
                signup_window['-MSG-'].update("Error: All fields are required.", text_color="red")
            else:

                success = create_account(
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