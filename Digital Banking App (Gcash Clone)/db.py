#db.py
import random
from datetime import datetime
user_db = {
    "NyanNyanNeko99": {
        "name": "Elise Villanueva Dela Cruz",
        "email": "evdelacruz@gmail.com",
        "password": "neko123",
        "pin": "6796",
        "balance": 52000.00
    },
    "originalstarman": {
        "name": "John Johndice Dez",
        "email": "jjdez@yahoomail.com",
        "password": "starman123",
        "pin": "4207",
        "balance": -10.00
    },
    "1": {
        "name": "admin",
        "email": "",
        "password": "",
        "pin": "",
        "balance": 0.00
    }
}
def gen_reciept_data(recipient, amount, transaction_type):
    """Generates a reciept for any transaction."""
    ref_num = f"AR-{random.randint(100000000, 999999999)}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "recipient": recipient,
        "amount": amount,
        "type": transaction_type,
        "timestamp": timestamp,
        "ref_num": ref_num
    }

def getbal(username):
    """Returns a user's balance."""
    if username in user_db:
        return user_db[username]["balance"]
    return None

def update_bal(username, amount):
    """This updates the user's balance."""
    if username in user_db:
        user_db[username]["balance"] += amount
        return user_db[username]["balance"]
    return None