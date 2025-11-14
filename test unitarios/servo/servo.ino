#include <Servo.h>
const int servoPin = 5;
Servo myServo;

void setup() {
  Serial.begin(9600);
  myServo.attach(servoPin);

}

void loop() {
  myServo.write(90);
  delay(5000);
  myServo.write(0);
  delay(5000);
  for (pos = 0; pos <= 180; pos += 1) { 
    myServo.write(pos);             
    delay(15);                      
  }
  for (pos = 180; pos >= 0; pos -= 1) { 
    myServo.write(pos);              
    delay(15);         
}