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

void jobSelect(Player& currentPlayer){
int choice;
  cout << "Tell me... How do you wish to live in this world?" << endl;
  cout << "1. To use your knowledge in Aura Dynamics to mog your opponents." << endl;
  cout << "2. To brawl it out with your enemies, and die in glorious battle." << endl;
  cout << "3. To be flexible enough to handle any type of opponent." << endl;
  cout << "4. To start from the bottom and make your way to the top. (Not for the faint of heart)" << endl;
  cin >> choice;
  currentPlayer.setClass(choice);
  cout << currentPlayer.desc << currentPlayer.jobTitle << ". You have been blessed with an aura of " << currentPlayer.aura << endl;
  delay(2);
  cout << "Hmm... An interesting choice." << endl;
}
int main(){
Player player1;

    intro();
    delay (3);
    
    jobSelect(player1);


    return 0;
}