#include <iostream>
#include <ctime>
#include <cstdlib>
using namespace std;

int main (){
    bool start = true;
    bool Calcrun;

while (start){
    cout << "Welcome to Vekkir's primitive calculator." << endl;
    cout << "Would you like to begin? [y/n] or view the help menu? [h]: "
    cin >> ynh;

switch (ynh){
    case 'y':
        cout << "Insert your numbers and operators." << endl;
        Calcrun = true;
        start = false;
        break;
    case 'n':
        cout << "See you around then.";
        break;
    case 'h'
        cout << "Instructions:\n 
            1. Insert any number\n 
            2. Insert an operator\n 
            3. When satisfied with input, enter '=' to calculate." 
            << endl;
        cout << "To begin, enter 'y'";
}
}

while (Calcrun){
    cout << "This is true.";
}

}