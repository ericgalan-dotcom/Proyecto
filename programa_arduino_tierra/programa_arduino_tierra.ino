#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX 
unsigned long nextMillis = 500;
void setup() {
   Serial.begin(9600);
   mySerial.begin(9600);
}
void loop() {
   if (Serial.available()) {
       String line = Serial.readString();
      mySerial.println(line);
      }
   }