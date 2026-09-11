import json
import os
import random
from datetime import datetime

class Database:
    def __init__(self, filename='database.json'):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.DB_FILE = os.path.join(self.BASE_DIR, filename)

        self.user_db = self.load_db()

    def load_db(self):
        """Loads the database from the JSON file, or creates one if it is missing."""
        if not os.path.exists(self.DB_FILE):
            default_db = {}
            with open(self.DB_FILE, 'w') as file:
                json.dump(default_db, file, indent=4)
                return default_db

        with open(self.DB_FILE,'r') as file:
            return json.load(file)

    def save_db(self):
        """Writes the current user_db to the JSON file"""
        with open(self.DB_FILE, 'w') as file:
            json.dump(self.user_db, file, indent=4)

    def create_account(self, username, name, email, password, pin):
        """Creates a new account and saves it to the database."""
        if username in self.user_db:
            return False

        self.user_db[username] = {
            "name" : name,
            "email" : email,
            "password": password,
            "pin": pin,
            "balance": 0.00
        }
        self.save_db()
        return True

    def gen_reciept_data(self, recipient, amount, transaction_type):
        """Generates a receipt for any transaction."""
        ref_num = f"AR-{random.randint(100000000, 999999999)}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "recipient": recipient,
            "amount": amount,
            "type": transaction_type,
            "timestamp": timestamp,
            "ref_num": ref_num
        }

    def getbal(self, username):
        """Returns a user's balance."""
        if username in self.user_db:
            return self.user_db[username]["balance"]
        return None

    def update_bal(self, username, amount):
        """This updates the user's balance."""
        if username in self.user_db:
            self.user_db[username]["balance"] += amount
            self.save_db()
            return self.user_db[username]["balance"]
        return None

    def send_money(self, sender, recipient, amount):
        """Deducts from sender and adds to recipient if funds allow."""
        if sender in self.user_db and recipient in self.user_db:
            if self.user_db[sender]["balance"] >= amount:
                self.user_db[sender]["balance"] -= amount
                self.user_db[recipient]["balance"] += amount
                self.save_db()
                return True, self.user_db[sender]["balance"]
            return False, "Insufficient balance."
        return False, "Recipient username not found."

# Initialize the object so main.py, auth.py, and dashboard.py can import it
bank_db = Database()