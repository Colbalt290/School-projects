#db.py
import json
import os
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(BASE_DIR, 'database.json')

default_db = {
    "student_1": {
        "name": "Juan Dela Cruz",
        "email": "juan@example.com",
        "password": "password123",
        "pin": "1234",
        "balance": 4250.00
    },
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
        "balance": 10.00
    }
}

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
        "balance": 10.00
    },
    "1": {
        "name": "admin",
        "email": "",
        "password": "",
        "pin": "",
        "balance": 0.00
    }
}

def load_db():
    """Loads the database from the JSON file, or creates one if it is missing."""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as file:
            json.dump(default_db, file, indent=4)
            return default_db

    with open(DB_FILE,'r') as file:
        return json.load(file)

def save_db():
    """Writes the current user_db to the JSON file"""
    with open(DB_FILE, 'w') as file:
        json.dump(user_db, file, indent=4)

user_db = load_db()

def create_account(username, name, email, password, pin):
    """Creates a new account and saves it to the database."""
    if username in user_db:
        return False

    user_db[username] = {
        "name" : name,
        "email" : email,
        "password": password,
        "pin": pin,
        "balance": 0.00
    }
    save_db()
    return True


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
        save_db()
        return user_db[username]["balance"]
    return None