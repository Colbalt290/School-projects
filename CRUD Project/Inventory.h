#pragma once
#include <iostream>
#include <vector>
#include <string>

struct Item{
    std::string name;
    int quantity;
};

class Inventory{
private:
    std::vector<Item> items; // List of Items

public: //CRUD
void createItem(std::string itemName, int qty);
void readInventory();
void updateItem(std::string itemName, int qty);
void deleteItem(std::string itemName);
};