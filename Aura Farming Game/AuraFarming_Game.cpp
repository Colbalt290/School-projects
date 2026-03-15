#include "player.h"
#include "delay.h"
#include <iostream>
#include <ctime>
#include <cstdlib>
#include <string>
using namespace std;

void intro(){
    cout << "Welcome to Aurion, where your Aura determines your place in this world..." <<  endl;
    cout << "This world will not treat you kindly, you must grow and cultivate your Aura to mog your enemies." << endl;
}

void jobSelect(){
  cout << "Select your Class." << endl;
  cout << " 1. Student \n 2. Professor \n 3. Master \n 4. Tarnished" << endl;
}
int main(){
    
    intro();
    delay (3);
    
    jobSelect();
    
    cout << "Hmm..." << endl;
        delay (1);

    return 0;
}