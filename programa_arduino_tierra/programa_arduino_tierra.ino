#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX

const int alarmaPin = 7; //Pin donde está conectado la alarma 
bool alarmaActiva = false;
int contadorini=0;
const int ledfalloDHT = 12;
const int ledfalloComs = 13;
// unsigned long nextMillis = 3000;
unsigned long lastReceiveTime = 0;
unsigned long nexttimeout = 0;
unsigned long timeouttime = 10000;
void setup() {
   pinMode(ledfalloDHT, OUTPUT);
   pinMode(ledfalloComs, OUTPUT);
   Serial.begin(9600);
   mySerial.begin(9600);
   pinMode(alarmaPin,OUTPUT);
   digitalWrite(alarmaPin, LOW);
   nexttimeout = millis() + timeouttime;
}
void loop() {
   // Enviar de tierra al satélite
    if (Serial.available()) {
       String line = Serial.readString();
      mySerial.println(line);
      if (line=="Iniciar\n" || line=="Reanudar\n"){
          contadorini=1;
      }
      if (line=="Parar\n"){
        contadorini=0;
      }
      }
    if (contadorini){
    if (millis() >= nexttimeout) { // donde ponemos esto
    Serial.println("FALLO de comunicación detectado");
    digitalWrite(alarmaPin, HIGH);  
    digitalWrite(ledfalloComs, HIGH);
  } else {
    digitalWrite(ledfalloComs, LOW);      // todo bien
    digitalWrite(alarmaPin, LOW);   // apagar alarma
  }
  }
  // Enviar del satélite a tierra
    if (mySerial.available()) {
         String data = mySerial.readString();
         Serial.println(data);
         nexttimeout = millis() + timeouttime;
       if (data=="FALLO") { 
      Serial.println("¡FALLO detectado!");  // :C
      digitalWrite(alarmaPin, HIGH);  // Enciende la alarma
      alarmaActiva = true;
      digitalWrite(ledfalloDHT, HIGH);

      }  else {
      if (alarmaActiva) {
        digitalWrite(alarmaPin, LOW);   // Apaga la alarma
        alarmaActiva = false;
        digitalWrite(ledfalloDHT, LOW);
      }
    }
  }

}