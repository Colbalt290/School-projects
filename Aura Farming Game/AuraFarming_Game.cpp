#include "player.h"
#include "delay.h"
#include <iostream>
#include <ctime>
#include <cstdlib>
#include <string>
using namespace std;

void intro(){
    cout << "Welcome to Aurion, where your Aura determines your place in this world..." <<  endl;
    delay (1);
    cout << "This world will not treat you kindly, you must grow and cultivate your Aura to mog your enemies." << endl;
}

void jobSelect(){
int choice;
  cout << "Tell me... How do you wish to live in this world?" << endl;
  cout << " 1. Student \n 2. Professor \n 3. Master \n 4. Tarnished" << endl;
  cin >> choice;
}
int main(){
    
    intro();
    delay (3);
    
    jobSelect();
    
    cout << "Hmm..." << endl;
        delay (1);

    return 0;
}