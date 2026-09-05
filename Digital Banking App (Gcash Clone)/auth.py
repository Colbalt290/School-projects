from db import user_db,getbal

def verify_login(username, password):
    """If returns True if credentials match, otherwise False."""

    #A precheck if the user exists in the database
    if username in user_db:
        #Checks for the correct username and password
        if user_db[username]["password"] == password:
            return True
    return False

#testing code:            
#username = input("Please enter your username:")
#password = input("Please enter your password:")

#if verify_login(username,password) is True:
    #logged_u = username
    #curr_bal = getbal(logged_u)
    #print(f"Welcome, {username}!",f"Your account balance is: {curr_bal}")

#else:
    #print("Wrong username or password!")