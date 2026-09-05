#db.py
user_db = {
    "NyanNyanNeko99": {
        "password": "nekogirldaisuki",
        "balance": 52000.00
    },
    "originalstarman": {
        "password": "starmanisbroke1999",
        "balance": -10.00
    }
}

def getbal(username):
    """Returns a user's balance."""
    if username in user_db:
        return user_db[username]["balance"]
    return None