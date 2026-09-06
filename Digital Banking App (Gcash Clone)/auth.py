from db import user_db

def verify_login(identifier, secret):
    """Verifies if user data matches existing data on db.py"""

    for username, account_data in user_db.items():
        if identifier == username or identifier == account_data.get("email"):
            if secret == account_data.get("password") or secret == account_data.get("pin"):
                return username
    return None

#testing code:            
#username = input("Please enter your username:")
#password = input("Please enter your password:")

#if verify_login(username,password) is True:
    #logged_u = username
    #curr_bal = getbal(logged_u)
    #print(f"Welcome, {username}!",f"Your account balance is: {curr_bal}")

#else:
    #print("Wrong username or password!")