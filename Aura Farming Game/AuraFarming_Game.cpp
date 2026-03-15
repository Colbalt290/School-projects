#include "player.h"
#include <iostream>
#include <ctime>
#include <cstdlib>
#include <string>
#include <thread>
#include <chrono>
using namespace std;



void getPlayerInfo(){
    cout << "What is your age?: ";
    cin >> age;
    cout << "What is your name?: ";
    cin >> name;
    cout << "So you're " << name << " aged " << age << endl;
}

void delay(int sec){
    this_thread::sleep_for(chrono::seconds(sec));
}

void initialAura(){

    int nameVal = name.length();

    if (age <= 16){
        cout << "Your total aura is: " << age + nameVal << endl;
            delay(1);
        cout << "You have too little aura, young one." << endl;
        cout << "Come back once you've grown a little bit more." << endl;
        break;
    } else {
        cout << "Your total aura is: " << (age * 2) + nameVal + aura << endl;
            delay(1);
        cout << "You have strong aura!" << endl;
    }
}
void jobSelect(){
  cout << "Select your Class." << end;
  cout << " 1. Student \n 2. Professor \n 3. Master \n 4. Tarnished" << endl;
  cin >> choice;

}
int main(){
    
    cout << "Welcome, Aura Farmer." << endl;
        delay (3);
    
    getPlayerInfo();
    
    cout << "Hmm..." << endl;
        delay (1);

    initalAura();
    return 0;
}