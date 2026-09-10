class ATM():
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.transactions = []

    def deposit(self, account, amount):
        account.current_balance += amount
        self.transactions.append(f"Deposited {amount} to Account {account.account_number}")
        print("Deposit Complete.")

    def withdraw(self, account, amount):
        account.current_balance -= amount
        self.transactions.append(f"Withdrew {amount} from Account {account.account_number}")
        print("Withdraw Complete.")

    def check_currentbalance(self, account):
        print(account.current_balance)

    def view_transactionsummary(self):
        print("=== Transaction Summary ===")
        if not self.transactions:
            print("No transactions recorded.")
        else:
            for transaction in self.transactions:
                print(transaction)