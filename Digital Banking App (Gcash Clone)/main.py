import PySimpleGUI as sg
import time
from db import user_db, getbal, update_bal
from auth import verify_login
from login import open_login
from dashboard import open_dashboard

if __name__ == '__main__':
    while True:
        logged_in_user = open_login()

        if logged_in_user is None:
            break

        current_balance = getbal(logged_in_user)
        open_dashboard(logged_in_user, current_balance)