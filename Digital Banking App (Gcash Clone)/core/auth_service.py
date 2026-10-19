from .database import Database, bank_db


class AuthService:
    """
    Business Logic Layer for User Authentication and Account Registration.
    """
    def __init__(self, db: Database = None):
        self.db = db if db is not None else bank_db

    @property
    def user_db(self):
        return self.db.user_db

    def create_account(self, username: str, name: str, email: str, password: str, pin: str) -> tuple:
        """
        Validates and creates a new user account.
        Returns: (success: bool, message: str)
        """
        username = username.strip() if username else ""
        name = name.strip() if name else ""
        email = email.strip() if email else ""
        password = password.strip() if password else ""
        pin = pin.strip() if pin else ""

        if not all([username, name, email, password, pin]):
            return False, "All fields are required."

        if len(pin) != 4 or not pin.isdigit():
            return False, "PIN must be exactly 4 numeric digits."

        self.db.load_db()

        if username in self.user_db:
            return False, f"Username '{username}' already exists."

        # Check if email is already registered
        for existing_user, data in self.user_db.items():
            if data.get("email", "").lower() == email.lower():
                return False, f"An account with email '{email}' already exists."

        self.user_db[username] = {
            "name": name,
            "email": email,
            "password": password,
            "pin": pin,
            "balance": 0.00,
            "inbox": []
        }
        self.db.save_db()
        return True, "Account created successfully."

    def login(self, identifier: str, secret: str) -> tuple:
        """
        Authenticates a user by username or email, and password or PIN.
        Returns: (success: bool, canonical_username: str|None, error_message: str|None)
        """
        self.db.load_db()
        identifier = identifier.strip() if identifier else ""
        secret = secret.strip() if secret else ""

        if not identifier or not secret:
            return False, None, "Please enter your username/email and password/PIN."

        for username, data in self.user_db.items():
            match_ident = (identifier == username or identifier.lower() == data.get("email", "").lower())
            match_secret = (secret == data.get("password") or secret == data.get("pin"))

            if match_ident and match_secret:
                return True, username, None

        return False, None, "Invalid username/email or password/PIN."

    def verify_login(self, identifier: str, secret: str) -> str:
        """
        Legacy/convenience method: Returns canonical username if valid, else None.
        """
        success, username, _ = self.login(identifier, secret)
        return username if success else None


# Default service singleton instance
auth_service = AuthService(bank_db)

