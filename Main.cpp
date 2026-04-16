#include <iostream>
#include <chrono>
using namespace std;
    #include <stdio.h> 
    int main(void) { 
        FILE *f = fopen("file","w"); 
        float f; 
        fputs("12A",f); 
        fclose(f); 
        f = fopen("file","r"); 
        fscanf(f,"%f",&f); 
        fclose(f); 
        printf("%f",f); 
        return 0; 
    } 