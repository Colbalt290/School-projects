import random
from datetime import datetime, timedelta
from .database import Database, bank_db


class BankService:
    """
    Business Logic Layer for Aurion Banking Operations.
    Handles balances, transactions, cash-out code generation/redemption,
    inbox notifications, and receipts.
    """
    def __init__(self, db: Database = None):
        self.db = db if db is not None else bank_db

    @property
    def user_db(self):
        return self.db.user_db

    def censor_name(self, name: str) -> str:
        """Censors middle/last letters of name parts for privacy (e.g. 'John Doe' -> 'J*** D**')."""
        parts = name.split()
        return " ".join([p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in parts])

    def add_inbox_notification(self, username: str, message: str) -> None:
        """Pushes a new notification to the top of the user's inbox list."""
        if username in self.user_db:
            if "inbox" not in self.user_db[username]:
                self.user_db[username]["inbox"] = []
            self.user_db[username]["inbox"].insert(0, message)

    def get_inbox(self, username: str) -> list:
        """Returns the inbox messages list for the given user."""
        if username in self.user_db:
            return self.user_db[username].get("inbox", [])
        return []

    def gen_receipt_data(self, recipient_name: str, amount: float, trans_type: str) -> dict:
        """Generates receipt dict matching exact requirements."""
        return {
            "recipient": recipient_name,
            "amount": amount,
            "type": trans_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trans_num": f"TXN-{random.randint(10000, 99999)}",
            "ref_num": f"AR-{random.randint(100000000, 999999999)}"
        }

    def check_expired_cashouts(self, username: str = None) -> None:
        """Checks for pending cashout codes that have expired and refunds the balance."""
        self.db.load_db()
        now = datetime.now()
        updated = False

        users_to_check = [username] if username and username in self.user_db else list(self.user_db.keys())

        for u in users_to_check:
            user_data = self.user_db.get(u, {})
            cashouts = user_data.get("cashouts", {})
            for code, record in list(cashouts.items()):
                if record.get("status") == "PENDING":
                    expires_at = datetime.fromisoformat(record["expires_at"])
                    if now > expires_at:
                        record["status"] = "EXPIRED"
                        user_data["balance"] += record["amount"]

                        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                        refund_msg = (
                            f"[{timestamp}] Cash-out code {code} expired. "
                            f"PHP {record['amount']:,.2f} refunded."
                        )
                        self.add_inbox_notification(u, refund_msg)
                        updated = True

        if updated:
            self.db.save_db()

    def get_balance(self, username: str) -> float:
        """Automatically checks for expired codes before returning the current balance."""
        if username in self.user_db:
            self.check_expired_cashouts(username)
            return self.user_db[username].get("balance", 0.0)
        return 0.0

    # Alias for backwards compatibility
    getbal = get_balance

    def cash_in(self, username: str, amount: float) -> tuple:
        """
        Adds funds to user's balance.
        Returns: (success: bool, new_balance_or_error: float|str, receipt: dict|None)
        """
        if username not in self.user_db:
            return False, "User not found.", None
        if amount <= 0:
            return False, "Cash-in amount must be greater than zero.", None

        self.user_db[username]["balance"] += amount
        self.db.save_db()

        receipt = self.gen_receipt_data(
            self.user_db[username].get("name", username),
            amount,
            "Cash In"
        )
        return True, self.user_db[username]["balance"], receipt

    def cash_out(self, username: str, amount: float) -> tuple:
        """
        Deducts funds directly (non-kiosk).
        Returns: (success: bool, new_balance_or_error: float|str, receipt: dict|None)
        """
        if username not in self.user_db:
            return False, "User not found.", None
        if amount <= 0:
            return False, "Invalid cash-out amount.", None
        if self.user_db[username]["balance"] < amount:
            return False, "Insufficient balance.", None

        self.user_db[username]["balance"] -= amount
        self.db.save_db()

        receipt = self.gen_receipt_data(
            self.user_db[username].get("name", username),
            amount,
            "Cash Out"
        )
        return True, self.user_db[username]["balance"], receipt

    def generate_cashout_code(self, username: str, amount: float, validity_minutes: int = 5) -> tuple:
        """
        Deducts balance and creates a temporary 6-digit reference code for kiosk redemption.
        Returns: (success: bool, code_or_error: str, formatted_expiry: str|None, new_balance: float|None)
        """
        self.db.load_db()
        if username not in self.user_db:
            return False, "User not found.", None, None

        if amount <= 0:
            return False, "Amount must be greater than 0.", None, None

        self.check_expired_cashouts(username)

        if self.user_db[username]["balance"] < amount:
            return False, "Insufficient balance.", None, None

        self.user_db[username]["balance"] -= amount

        code = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=validity_minutes)

        if "cashouts" not in self.user_db[username]:
            self.user_db[username]["cashouts"] = {}

        self.user_db[username]["cashouts"][code] = {
            "amount": amount,
            "expires_at": expires_at.isoformat(),
            "status": "PENDING"
        }

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.add_inbox_notification(
            username,
            f"[{timestamp}] Cash-Out Requested: Code {code} created for PHP {amount:,.2f}."
        )
        self.db.save_db()

        formatted_time = expires_at.strftime("%I:%M %p")
        return True, code, formatted_time, self.user_db[username]["balance"]

    def redeem_cashout_code(self, code: str) -> tuple:
        """
        Redeems a 6-digit kiosk reference code and dispenses cash.
        Returns: (success: bool, message: str, receipt: dict|None)
        """
        self.db.load_db()
        self.check_expired_cashouts()

        for username, user_data in self.user_db.items():
            cashouts = user_data.get("cashouts", {})
            if code in cashouts:
                record = cashouts[code]

                if record.get("status") == "EXPIRED":
                    return False, "Code has expired! Funds have been refunded to the user's account.", None

                if record.get("status") != "PENDING":
                    return False, f"Code is no longer valid (Status: {record.get('status')}).", None

                record["status"] = "COMPLETED"
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                self.add_inbox_notification(
                    username,
                    f"[{timestamp}] Kiosk Cash-Out Completed: PHP {record['amount']:,.2f} dispensed."
                )
                self.db.save_db()

                receipt = self.gen_receipt_data(
                    user_data.get("name", username),
                    record["amount"],
                    "Kiosk Cash Out"
                )
                return True, "Cash out successful! Kiosk dispensed cash.", receipt

        return False, "Invalid reference code.", None

    def send_money(self, sender: str, recipient_un: str, amount: float) -> tuple:
        """
        Transfers money from sender to recipient.
        Returns: (success: bool, new_balance_or_error: float|str, receipt: dict|None)
        """
        self.db.load_db()
        if sender == recipient_un:
            return False, "You cannot send money to yourself.", None

        if amount <= 0:
            return False, "Amount must be greater than zero.", None

        if sender not in self.user_db:
            return False, "Sender account not found.", None

        if recipient_un not in self.user_db:
            return False, "Recipient username not found.", None

        if self.user_db[sender]["balance"] < amount:
            return False, "Insufficient balance.", None

        self.user_db[sender]["balance"] -= amount
        self.user_db[recipient_un]["balance"] += amount

        sender_name = self.user_db[sender].get("name", sender)
        recipient_name = self.user_db[recipient_un].get("name", recipient_un)
        censored_sender = self.censor_name(sender_name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.add_inbox_notification(
            recipient_un,
            f"[{timestamp}] Received PHP {amount:,.2f} from {censored_sender}."
        )
        self.add_inbox_notification(
            sender,
            f"[{timestamp}] Sent PHP {amount:,.2f} to {recipient_name}."
        )
        self.db.save_db()

        receipt = self.gen_receipt_data(recipient_name, amount, "Send Money")
        return True, self.user_db[sender]["balance"], receipt

    def pay_bill(self, username: str, biller_name: str, amount: float) -> tuple:
        """
        Pays a bill/merchant.
        Returns: (success: bool, new_balance_or_error: float|str, receipt: dict|None)
        """
        self.db.load_db()
        if username not in self.user_db:
            return False, "User not found.", None

        if amount <= 0:
            return False, "Invalid payment amount.", None

        if not biller_name or not biller_name.strip():
            return False, "Biller/Merchant name is required.", None

        if self.user_db[username]["balance"] < amount:
            return False, "Insufficient balance.", None

        self.user_db[username]["balance"] -= amount
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.add_inbox_notification(
            username,
            f"[{timestamp}] Payment Successful: PHP {amount:,.2f} paid to {biller_name}."
        )
        self.db.save_db()

        receipt = self.gen_receipt_data(biller_name, amount, "Payment")
        return True, self.user_db[username]["balance"], receipt


# Default service singleton instance
bank_service = BankService(bank_db)

