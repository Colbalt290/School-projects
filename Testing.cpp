#include <iostream>
#include <iomanip>
#include <string>
using namespace std;

const int num[] = {1, 2, 3, 4, 5};

int main()
{
int sum;
  sum = 0;
  for (int i = 0; i < 5; i++){
    sum += num [i];
  }
  cout << sum;

}