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
        if not os.path.exists(self.DB_FILE):
            default_db = {}
            with open(self.DB_FILE, 'w') as file:
                json.dump(default_db, file, indent=4)
                return default_db

        with open(self.DB_FILE, 'r') as file:
            return json.load(file)

    def save_db(self):
        with open(self.DB_FILE, 'w') as file:
            json.dump(self.user_db, file, indent=4)

    def censor_name(self, name):
        parts = name.split()
        return " ".join([p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in parts])

    def get_inbox(self, username):
        if username in self.user_db:
            return self.user_db[username].get("inbox", [])
        return []

    def gen_receipt_data(self, recipient_name, amount, trans_type):
        """Generates receipt dict matching exact requirements."""
        return {
            "recipient": recipient_name,
            "amount": amount,
            "type": trans_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ref_num": f"AR-{random.randint(100000000, 999999999)}"
        }

    def cash_in(self, username, amount):
        if username in self.user_db and amount > 0:
            self.user_db[username]["balance"] += amount
            self.save_db()
            receipt = self.gen_receipt_data(
                self.user_db[username].get("name", username),
                amount,
                "Cash In"
            )
            return True, self.user_db[username]["balance"], receipt
        return False, "Invalid cash-in amount.", None

    def cash_out(self, username, amount):
        if username in self.user_db and amount > 0:
            if self.user_db[username]["balance"] >= amount:
                self.user_db[username]["balance"] -= amount
                self.save_db()
                receipt = self.gen_receipt_data(
                    self.user_db[username].get("name", username),
                    amount,
                    "Cash Out"
                )
                return True, self.user_db[username]["balance"], receipt
            return False, "Insufficient balance.", None
        return False, "Invalid cash-out amount.", None

    def send_money(self, sender, recipient_un, amount):
        if sender == recipient_un:
            return False, "You cannot send money to yourself.", None

        if sender in self.user_db and recipient_un in self.user_db:
            if self.user_db[sender]["balance"] >= amount:
                self.user_db[sender]["balance"] -= amount
                self.user_db[recipient_un]["balance"] += amount

                sender_name = self.user_db[sender].get("name", sender)
                recipient_name = self.user_db[recipient_un].get("name", recipient_un)
                censored_sender = self.censor_name(sender_name)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Push inbox notification to recipient
                notification = f"[{timestamp}] Received {amount:,.2f} PHP from {censored_sender}."
                if "inbox" not in self.user_db[recipient_un]:
                    self.user_db[recipient_un]["inbox"] = []
                self.user_db[recipient_un]["inbox"].insert(0, notification)

                self.save_db()

                receipt = self.gen_receipt_data(recipient_name, amount, "Send Money")
                return True, self.user_db[sender]["balance"], receipt
            return False, "Insufficient balance.", None
        return False, "Recipient username not found.", None

    def pay_bill(self, username, biller_name, amount):
        if username in self.user_db and amount > 0:
            if self.user_db[username]["balance"] >= amount:
                self.user_db[username]["balance"] -= amount
                self.save_db()
                receipt = self.gen_receipt_data(biller_name, amount, "Payment")
                return True, self.user_db[username]["balance"], receipt
            return False, "Insufficient balance.", None
        return False, "Invalid amount.", None

    def getbal(self, username):
        if username in self.user_db:
            return self.user_db[username]["balance"]
        return 0.0

    def create_account(self, username, name, email, password, pin):
        """Creates a new account and saves it to the database."""
        if username in self.user_db:
            return False

        self.user_db[username] = {
            "name": name,
            "email": email,
            "password": password,
            "pin": pin,
            "balance": 0.00,
            "inbox": []
        }
        self.save_db()
        return True

# Initialize the object so main.py, auth.py, and dashboard.py can import it
bank_db = Database()