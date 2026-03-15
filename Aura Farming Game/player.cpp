#include "player.h"
using namespace std;

void Player::setClass(int choice){
switch (choice) {
        case 1:
            jobTitle = "Mage";
            desc = "Your thirst for knowledge knows no bounds, for you the more knowledge the more Aura you have. A ";
            aura = 140;
            hp = 50;
            break;
        case 2:
            jobTitle = "Fighter";
            desc = "To fight is your calling, for it is the only thing you know since birth. A ";
            aura = 50;
            hp = 120;
            break;
        case 3:
            jobTitle = "Rouge";
            desc = "You are a jack of all trades, yet a master of none, still oftentimes better than a master one. A ";
            aura = 100;
            hp = 100;
            break;
        case 4:
            jobTitle = "Tarnished";
            desc = "You have chosen the path of pain and suffering for you are the lowest of the lows... A ";
            aura = 10;
            hp = 10;
            break;
        case 69:
            jobTitle = "Lord of Sex";
            desc = "Hahahaha you sex everyone for you are The ";
            aura = 69000;
            hp = 69000;
    }
}