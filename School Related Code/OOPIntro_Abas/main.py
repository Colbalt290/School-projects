"""
    main.py
"""
import Accounts
import ATM

Account1 = Accounts.Accounts(account_number=123456,account_firstname="Psalm",
                            account_lastname="Psalm",current_balance = 7272727,
                            address = "Silver Grove City",
                            email = "pvabas@mymail.mapua.edu.ph")

print("Account 1")
print(Account1.account_firstname)
print(Account1.account_lastname)
print(Account1.current_balance)
print(Account1.address)
print(Account1.email)

print()

Account2 = Accounts.Accounts(account_number=654321,account_firstname="John",
                            account_lastname="MAAAAAAAAX",current_balance = 99999,
                            address = "The Commonwealth",
                            email = "maximum129@yahoo.com")

print("Account 2")
print(Account2.account_firstname)
print(Account2.account_lastname)
print(Account2.current_balance)
print(Account2.address)
print(Account2.email)

# Creating and Using an ATM object and initialize with a serial number
ATM1 = ATM.ATM(98765432)

# Perform transactions
ATM1.deposit(Account1, 727)
ATM1.check_currentbalance(Account1)

ATM1.deposit(Account2, 999)
ATM1.check_currentbalance(Account2)

print()
# Display all transactions made
ATM1.view_transactionsummary()

# Display serial number at the end of the program
print(f"ATM Serial Number: {ATM1.serial_number}")