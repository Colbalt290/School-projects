#include "delay.h"
#include <thread>
#include <chrono>

void delay(int sec){
    std::this_thread::sleep_for(std::chrono::seconds(sec));
}