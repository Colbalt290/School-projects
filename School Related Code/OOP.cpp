#include <iostream>
#include <string>
using namespace std;

class BankAccount {
    private:
            double balance;
    public:
        BankAccount(double initialBalance){
        balance=initialBalance;
    }

    void deposit(double amount){
        if (amount>0){
            balance += amount;
            cout<<"Deposited: " << amount <<endl;
            cout << "New Balance: " << balance << endl;
            }
    }
};


int main(){
BankAccount myAccount(1000);
myAccount.deposit(500);
return 0;
}