#include <iostream>
#include <ctime>
#include <cstdlib>
using namespace std;
char opt;

void clear (){
    #ifdef _WIN32
        system("cls");
    #else
        system("clear");
    #endif
}
void startApp (){
clear();
switch (opt){
    case 'y': {
    double total;
    double nextNum;
    char op;

        cout << "Insert your first number:" << endl;
        cin >> total;

    while (true){
        cout << "Enter an Operation [+, -, *, /] or [=] to see result: " << endl;
        cin >> op;

    if (op == '='){
        cout << "Result: " << total << endl;    
        break;
    }

    cout << "Next number: " <<endl;
    cin >> nextNum;

    switch (op){
        case '+':
            total += nextNum;
            break;
        case '-':
            total -= nextNum;
            break;
        case '*':
            total *= nextNum;
            break;
        case '/':
        if (nextNum != 0){
            total /= nextNum;
        } else {
            cout << "Cannot divide by zero." << endl;
        }
        break;
        default:
            cout << "Wrong operator." << endl;
            break;
    }

    }
        break;
}
    case 'h':
    cout << "Instructions:\n"
         << "1. Insert any number\n"
         << "2. Insert an operator\n"
         << "3. When satisfied with input, enter '=' to calculate.\n" 
         << endl;
}
}

int main (){
    cout << "Welcome to Vekkir's primitive calculator." << endl;

while (true){
    cout << "Would you like to begin? [y/n] or view the help menu? [h]: " << endl;
    cin >> opt;

if (opt == 'n'){
    cout << "See you around." << endl;
    break;
}
    startApp();
    }
    return 0;
}