#include <iostream>
#include <ctime>
#include <cstdlib>
#include <string>
#include <thread>
#include <chrono>
using namespace std;

class Player {
public:
        int age, aura, hp;
        string name, jobTitle;

        void setClass (int choice){
            switch (choice){
                case 1:
                    jobTitle = "Student";
                    aura = 20;
                    hp = 100;
                    break;
                
                case 2:
                    jobTitle = "Professor";
                    aura = 40;
                    hp = 120;
                    break;
                
                case 3:
                    jobTitle = "Master";
                    aura = 100;
                    hp = 50;
                    break;

                case 4:
                    jobTitle = "Tarnished";
                    aura = 0;
                    hp = 100;
                    break;
            }
        }
}

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
    } else {
        cout << "Your total aura is: " << (age * 2) + nameVal + aura << endl;
            delay(1);
        cout << "You have strong aura!" << endl;
    }
}
void jobSelect(){
  cout << "Select your Class."
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