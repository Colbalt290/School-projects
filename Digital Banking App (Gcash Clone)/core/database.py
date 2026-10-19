import os
import json


class Database:
    """
    Low-level persistence layer for Aurion Banking.
    Manages reading and writing data to database.json.
    """
    def __init__(self, filename="database.json", base_dir=None):
        if base_dir is None:
            # Resolves to project root (parent directory of 'core')
            self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.BASE_DIR = base_dir

        self.DB_FILE = os.path.join(self.BASE_DIR, filename)
        self.user_db = self.load_db()

    def load_db(self):
        """Loads and returns the user database dictionary from JSON file."""
        if not os.path.exists(self.DB_FILE):
            default_db = {}
            with open(self.DB_FILE, "w", encoding="utf-8") as file:
                json.dump(default_db, file, indent=4)
            self.user_db = default_db
            return self.user_db

        with open(self.DB_FILE, "r", encoding="utf-8") as file:
            try:
                self.user_db = json.load(file)
            except json.JSONDecodeError:
                self.user_db = {}
            return self.user_db

    def save_db(self):
        """Saves current state of user_db to JSON file."""
        with open(self.DB_FILE, "w", encoding="utf-8") as file:
            json.dump(self.user_db, file, indent=4)

    def get_user(self, username):
        """Returns account dict for username, or None if not found."""
        return self.user_db.get(username)

    def user_exists(self, username):
        return username in self.user_db

    def find_username_by_identifier(self, identifier):
        """Finds canonical username matching either username or email."""
        for username, data in self.user_db.items():
            if identifier == username or identifier.lower() == data.get("email", "").lower():
                return username
        return None

    # ==========================================
    # Backwards Compatibility Delegations
    # ==========================================
    def getbal(self, username):
        from .bank_service import bank_service
        return bank_service.get_balance(username)

    def cash_in(self, username, amount):
        from .bank_service import bank_service
        return bank_service.cash_in(username, amount)

    def cash_out(self, username, amount):
        from .bank_service import bank_service
        return bank_service.cash_out(username, amount)

    def send_money(self, sender, recipient, amount):
        from .bank_service import bank_service
        return bank_service.send_money(sender, recipient, amount)

    def pay_bill(self, username, biller_name, amount):
        from .bank_service import bank_service
        return bank_service.pay_bill(username, biller_name, amount)

    def generate_cashout_code(self, username, amount, validity_minutes=5):
        from .bank_service import bank_service
        return bank_service.generate_cashout_code(username, amount, validity_minutes)

    def redeem_cashout_code(self, code):
        from .bank_service import bank_service
        return bank_service.redeem_cashout_code(code)

    def check_expired_cashouts(self, username=None):
        from .bank_service import bank_service
        return bank_service.check_expired_cashouts(username)

    def get_inbox(self, username):
        from .bank_service import bank_service
        return bank_service.get_inbox(username)

    def add_inbox_notification(self, username, message):
        from .bank_service import bank_service
        return bank_service.add_inbox_notification(username, message)

    def create_account(self, username, name, email, password, pin):
        from .auth_service import auth_service
        success, _ = auth_service.create_account(username, name, email, password, pin)
        return success


# Default database singleton instance
bank_db = Database()

