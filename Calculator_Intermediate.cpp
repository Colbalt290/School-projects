#include <iostream>
#include <ctime>
#include <cstdlib>
using namespace std;

int main(){
  int num1, num2;
  char answer, y, n, operation;
  bool Isrunning = true;
  bool Isrunning2 = false;
  bool getout = false;
  
  while (Isrunning){
    cout << "Enter y to continue or n to exit: ";
    cin >> answer;
    switch (answer) {
      case 'y':
        cout << "Welcome back." << endl;
        Isrunning2 = true;
        getout = true;
        Isrunning = false;
        break;
      case 'n':
        cout << "Bye Bye." << endl;
        Isrunning = false;
        break;
    }
  }
  //Code below is for the calculator.
  while (Isrunning2){
    cout << "Enter your first number: ";
    cin >> num1;
    cout << "Enter your second number: ";
    cin >> num2;
    cout << "Enter your operation (+ , - , *, /): ";
    cin >> operation;
    switch (operation){
      case '+':
        cout << "Result: " << num1 + num2 << endl;
        break;
      case '-':
        cout << "Result: " << num1 - num2 << endl;
        break;
      case '*':
        cout << "Result: " << num1 * num2 << endl;
        break;
      case '/':
        if (num2 == 0){
          cout << "Cannot divide by zero." << endl;
          break;
        } else {
          cout << "Result: " << num1 / num2 << endl;
          break;
        }
    default:
      cout << "Invalid operation selected." << endl;
      break;
    }
  char stop;
  cout << "Continue? y/n: ";
  cin >> stop;
    if (stop == 'n'){
      cout << "Goodbye!";
      Isrunning2 = false;
      break;
  }
 }
}