#include <iostream>
#include <ctime>
#include <cstdlib>
using namespace std;

int main (){
  srand (time (0));
  bool IsRunning = true;
  char y, n, answer;

while (IsRunning){

int diceroll = (rand() % 6 + 1);
  cout << "===============================" << endl;
  cout << "Roll the dice? y/n? " << endl;
  cin >> answer;

switch (answer){
  case 'y':
    cout << "Rolling the Dice..." << endl;
    cout << "You got a: " << (rand() % 6 + 1) << endl;
    break;
  
  case 'n':
    cout << "Goodbye." << endl;
    IsRunning = false;
    break;
  
  default:
    cout << "Enter y to continue or n to stop. " << endl;
    }

  cout << "===============================" << endl;

  }
  
return 0;
}