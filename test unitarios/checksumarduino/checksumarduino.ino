#include <stdio.h>
#include <string.h>
  
int main(){
float t = 23.40;
float h = 52.00;
float dist = 30.40;
float ang = 15.00;
char check[64] = "";
char buffer[50];




  strcat(check, "T");
  sprintf(buffer, "%.2f", t);
  strcat(check, buffer);

  strcat(check, "H");
  sprintf(buffer, "%.2f", h);
  strcat(check, buffer);

  strcat(check, "D");
  sprintf(buffer, "%.2f", dist);
  strcat(check, buffer);

  strcat(check, "A");
  sprintf(buffer, "%.2f", ang);
  strcat(check, buffer);

  printf("%s",check);
  unsigned int checksum = 0;
  for (int q = 0; check[q] != '\0'; q++) {
    checksum += (unsigned char)check[q];
  }
  checksum %= 256;
  printf("%d\n",checksum);
}