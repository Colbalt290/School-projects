#include <iostream>
#include <ctime>
#include <cstdlib>
using namespace std;

int main (){
    srand (time (0));
    bool Isrunning = true;
    char answer;

while (Isrunning){
    int coin = (rand () % 2 + 1);
    cout << "Heads or Tails? [h,t]: ";
    cin >> answer;
    

switch (answer){
    
    case 'h':
        cout << "Flipping " << endl;
        cout << endl;
        
        if (coin == 1){
            cout << "====================" << endl;
            cout << "|You guessed right!|" << endl;
            cout << "====================" << endl;
            cout << endl;
            break;
        } else {
            cout << "===============================" << endl;
            cout << "|You got Tails. Guess again :)|" << endl;
            cout << "===============================" << endl;
            cout << endl;
            break;
        }

    case 't':
        cout << "Flipping " << endl;
        cout << endl;
        
        if (coin == 2){
            cout << "====================" << endl;
            cout << "|You guessed right!|" << endl;
            cout << "====================" << endl;
            cout << endl;
            break;
        } else {
            cout << "===============================" << endl;
            cout << "|You got Heads. Guess again :)|" << endl;
            cout << "===============================" << endl;
            cout << endl;
            break;
        }

    default:
        cout << endl;
        cout << "Wrong input, please input h or t." << endl;
        cout << endl;
        break;
}
}
}