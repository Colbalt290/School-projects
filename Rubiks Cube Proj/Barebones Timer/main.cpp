#include <iostream>
#include <chrono>
#include "scramble.h"

using namespace std;
using namespace std::chrono;

int main(){
    cout << "<===Vekkir's Barebone Timer===>" << endl;

while (true){
    cout << "\n";
    gen();

    cout << "\nPress ENTER to start.";
    cin.get();

    auto start = high_resolution_clock::now();

    cout << "\nPress ENTER to stop.";
    cin.get();
    
    auto stop = high_resolution_clock::now();

    duration<double> time_span = duration_cast<duration<double>>(stop-start);

    cout << "\nSolve Time: " << time_span.count() << " seconds" << endl;
}
}