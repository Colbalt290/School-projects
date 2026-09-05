import PySimpleGUI as sg
import time
from db import user_db, getbal, update_bal
from auth import verify_login

def open_dashboard(entered_user, actual_bal):
    layout = [
        [sg.Text(f"Welcome back, {entered_user}!", font=('Segoe UI', 14, 'bold'))],
        [sg.Text(f"Current Balance: {actual_bal:,.2f} PHP", font=('Segoe UI', 18, 'bold'),key = '-BALANCE-')],
        [sg.Input(key='-AMOUNT-', size=(15,1)), sg.Button('Deposit',border_width=0)],
        [sg.Text("", size=(30,1), key='-DASH_MSG-')],
        [sg.Button('Logout', border_width=0)]
    ]

    dashboard_window = sg.Window('Dashboard', layout, margins=(40,40))

    while True:
        event, values = dashboard_window.read()
        if event == sg.WINDOW_CLOSED or event == 'Logout':
            break
        if event == 'Deposit':
            try:
                amount = float(values['-AMOUNT-'])

                if amount > 0:
                    new_bal = update_bal(entered_user, amount)

                    dashboard_window['-BALANCE-'].update(f"Current Balance: {new_bal:,.2f} PHP")
                    dashboard_window['-DASH_MSG-'].update(f"Successfully deposited {amount:,.2f} PHP!", text_color = "green")

                    dashboard_window['-AMOUNT-'].update("")
                else:
                    dashboard_window['-AMOUNT-'].update("")
                    dashboard_window['-DASH_MSG-'].update("Amount must be greater than 0.", text_color = "red")
            except ValueError:
                dashboard_window['-AMOUNT-'].update("")
                dashboard_window['-DASH_MSG-'].update("Error: Please enter a valid number.", text_color = "red")
    dashboard_window.close()

sg.theme('DarkTeal9')
sg.set_options(font=('Segoe UI', 11))

#Login window Layout
layout = [
          [sg.Text("Welcome to Aurion's Digital Banking Service.", font=('Segoe UI', 14, 'bold'), pad=(0, 10))],
          [sg.Text("Username:")],
          [sg.Input(key='-UN-')],
          [sg.Text("Password:")],
          [sg.Input(key='-PWORD-', password_char='*')],
          [sg.Text("", size=(40, 1), key='-OUTPUT-')],
          [sg.Button('Login', border_width=0), sg.Button('Quit', border_width=0)]
          ]

#Create the window
window = sg.Window('Aurion Banking Service', layout, margins=(20,20))

#Display and interact with the Window using an Event Loop
while True:
    event, values = window.read()
    #Check if user is wants to quit or window was closed
    if event == sg.WINDOW_CLOSED or event == 'Quit':
        break
    #Login Event
    if event == 'Login':
        entered_user = values['-UN-']
        entered_password = values['-PWORD-']

        if verify_login(entered_user, entered_password) is True:
            actual_bal = getbal(entered_user)
            
            #Closes the login window and opens the dashboard
            window.close()
            open_dashboard(entered_user, actual_bal)
            break
        else:
            window['-OUTPUT-'].update("Error: Invalid credentials.", text_color = "red")

#This is when they press quit instead.
window.close()