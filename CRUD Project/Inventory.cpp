#include "Inventory.h"
using namespace std;

void Inventory::createItem(string itemName, int qty){
    items.push_back({itemName, qty});
    cout << " [+] Created: " << itemName << " x" << qty << endl;
}

void Inventory::readInventory(){
    cout << "<=======Your Inventory======>" << endl;
    if (items.empty()){
        cout << " (Empty)" << endl;
        return;
    }
    for (size_t i = 0; i < items.size(); i++){
        cout << "  - " << items[i].name << " (Qty: " << items[i].quantity << ")" << endl;
    }
    cout << "<===========================>" << endl;
}

void Inventory::updateItem(string itemName, int newQty){
    for (size_t i = 0; i < items.size(); i++){
        if (items[i].name == itemName){
            items[i].quantity = newQty;
            cout << " [~] Updated: " << itemName << " to quantity " << newQty << endl;
            return;
        }
    }
    cout << " [!] Item '" << itemName << "' not found, cannot update." << endl;
}

void Inventory::deleteItem (string itemName){
    for (auto it = items.begin(); it != items.end(); ++it){
        if (it->name == itemName) {
            items.erase(it);
            cout << " [-] Deleted: " << itemName << " from Inventory." << endl;
            return;
        }
    }
    cout << " [!] Item '" << itemName << "' not found, cannot delete." << endl;
}