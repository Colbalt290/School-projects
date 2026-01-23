#include <iostream>
#include <string>
using namespace std;

bool unlockVault (string location, string code){
   const string masterCode = "8888";
   return (code == masterCode);
}

int main () {
 string input;
 bool accessGranted = false;
 cout << "---BANK VAULT SECURITY---" << endl;
 
 for (int i = 1; i <= 3; i++){
     cout << "Attempt " << i << "of 3. Enter Code: ";
     cin >> input;
 if (unlockVault ("Main Vault", input)){
     cout << "Access Granted! Opening Vault..." << endl;
     accessGranted = true;
     break;
 } else {
     cout << "Incorrect Code." << endl;
 }
 }
 if (!accessGranted) {
     cout << "Vault Locked. Security notified." << endl;
 }
 return 0;
 }
 

