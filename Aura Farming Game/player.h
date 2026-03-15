#pragma once
#include <string>

class Player{
    public:
    //Attributes
    int age, aura, hp;
    std::string name, jobTitle;

    void setClass(int choice);
};