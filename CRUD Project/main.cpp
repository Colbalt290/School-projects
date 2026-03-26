#include <iostream>
#include "Inventory.h"

using namespace std;

int main(){
    Inventory myBag;

    cout << "---CRUD TEST---" << endl;

    //Creation
    myBag.createItem("Energy Drink", 3);
    myBag.createItem("Number 2 Pencil", 1);

    //Reading
    myBag.readInventory();

    //Updating
    myBag.updateItem("Number 2 Pencil", 2);
    myBag.readInventory();

    //Deleting
    myBag.deleteItem("Energy Drink");
    myBag.readInventory();

    return 0;
}