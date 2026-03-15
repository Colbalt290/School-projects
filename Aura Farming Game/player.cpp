#include "player.h"
using namespace std;

void Player::setClass(int choice){
switch (choice) {
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