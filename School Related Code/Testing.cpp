 #include <iostream>
 #include <cstdlib> 
#include <string>
#include <cstring>
using namespace std; 
   struct S { 
        char *p; 
    }; 
    int main(void) { 
        char *p = "abcd"; 
        struct S S[2]; 
        int i; 
        for(i = 0; i < 2; i++) 
        	S[i].p = p + i; 
        cout<<S[1].p[0]; 
        return 0; 
    } 
    