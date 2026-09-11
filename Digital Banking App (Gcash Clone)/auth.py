from db import bank_db

class Authenticator:
    def verify_login(self, identifier, secret):
        """Verifies if user data matches existing data on db.py"""
        
        # Iterate over the user_db dictionary inside the bank_db object
        for username, account_data in bank_db.user_db.items():
            if identifier == username or identifier == account_data.get("email"):
                if secret == account_data.get("password") or secret == account_data.get("pin"):
                    return username
        return None

# Initialize the object so login.py can import the active security manager
auth = Authenticator()
#testing code:            
#username = input("Please enter your username:")
#password = input("Please enter your password:")

#if verify_login(username,password) is True:
    #logged_u = username
    #curr_bal = getbal(logged_u)
    #print(f"Welcome, {username}!",f"Your account balance is: {curr_bal}")

#else:
    #print("Wrong username or password!")