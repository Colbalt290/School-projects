"""
    main.py
"""
import Accounts
import ATM

Account1 = Accounts.Accounts(account_number=123456,account_firstname="Royce",
                            account_lastname="Chua",current_balance = 1000,
                            address = "Silver Street Quezon City",
                            email = "roycechua123@gmail.com")

print("Account 1")
print(Account1.account_firstname)
print(Account1.account_lastname)
print(Account1.current_balance)
print(Account1.address)
print(Account1.email)

print()

Account2 = Accounts.Accounts(account_number=654321,account_firstname="John",
                            account_lastname="Doe",current_balance = 2000,
                            address = "Gold Street Quezon City",
                            email = "johndoe@yahoo.com")

print("Account 2")
print(Account2.account_firstname)
print(Account2.account_lastname)
print(Account2.current_balance)
print(Account2.address)
print(Account2.email)

# Creating and Using an ATM object and initialize with a serial number
ATM1 = ATM.ATM(98765432)

# Perform transactions
ATM1.deposit(Account1, 500)
ATM1.check_currentbalance(Account1)

ATM1.deposit(Account2, 300)
ATM1.check_currentbalance(Account2)

print()
# Display all transactions made
ATM1.view_transactionsummary()

# Display serial number at the end of the program
print(f"ATM Serial Number: {ATM1.serial_number}")