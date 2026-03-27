#include "scramble.h"
#include <iostream>
#include <ctime>
#include <cstdlib>
#include "delay.h"
#include <string>

using namespace std;

void gen(){
    string moves[] = {
    "U", "U'", "U2", // 0, 1, 2
    "D", "D'", "D2", // 3, 4, 5
    "L", "L'", "L2", // 6, 7, 8
    "R", "R'", "R2", // 9, 10, 11
    "F", "F'", "F2", // 12, 13, 14
    "B", "B'", "B2"  // 15, 16, 17
};

srand(time(0));

int lastFace = -1;

cout << "Generating Scramble..." << endl;
delay(0.5);
for (int i = 0; i < 20; i++){
    int randIndex;
    int currentFace;

do {
    randIndex = rand() % 18;
    currentFace = randIndex / 3;
} while (currentFace == lastFace);

lastFace = currentFace;

cout << moves[randIndex] << " ";

}
cout << endl;
}

