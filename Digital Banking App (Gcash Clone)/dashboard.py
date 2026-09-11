import PySimpleGUI as sg
from db import bank_db

class DashboardScreen:
    def open_dashboard(self, entered_user):
        # Fetch the balance directly from the database object
        actual_bal = bank_db.getbal(entered_user)

        layout = [
            [sg.Text(f"Welcome back, {entered_user}!", font=('Segoe UI', 14, 'bold'))],
            [sg.Text(f"Current Balance: {actual_bal:,.2f} PHP", font=('Segoe UI', 18, 'bold'), key='-BALANCE-')],
            [sg.Input(key='-AMOUNT-', size=(15,1)), sg.Button('Deposit', border_width=0)],
            [sg.Text("", size=(30,1), key='-DASH_MSG-')],
            [sg.Button('Logout', border_width=0)]
        ]

        dashboard_window = sg.Window('Dashboard', layout, margins=(40,40))

        while True:
            event, values = dashboard_window.read()
            
            if event in (sg.WINDOW_CLOSED, 'Logout'):
                break
                
            if event == 'Deposit':
                try:
                    amount = float(values['-AMOUNT-'])

                    if amount > 0:
                        # Update balance using the bank_db object
                        new_bal = bank_db.update_bal(entered_user, amount)

                        dashboard_window['-BALANCE-'].update(f"Current Balance: {new_bal:,.2f} PHP")
                        dashboard_window['-DASH_MSG-'].update(f"Successfully deposited {amount:,.2f} PHP!", text_color="green")
                        dashboard_window['-AMOUNT-'].update("")
                    else:
                        dashboard_window['-AMOUNT-'].update("")
                        dashboard_window['-DASH_MSG-'].update("Amount must be greater than 0.", text_color="red")
                        
                except ValueError:
                    dashboard_window['-AMOUNT-'].update("")
                    dashboard_window['-DASH_MSG-'].update("Error: Please enter a valid number.", text_color="red")
                    
        dashboard_window.close()