#include <SoftwareSerial.h>
#include <DHT.h>
#include <Servo.h>

#define DHTPIN 2
#define DHTTYPE DHT11

Servo myservo;
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11);

const int trigpin=8;
const int echopin=7;
float duracion, dist;
unsigned long nextHT = 0;
unsigned long nextTimeoutHT = 0;
bool esperandoTimeout = false;
bool enviarDatos = false;
unsigned long ultimoEnvio = 0;
const unsigned long intervalo = 3000;  // cada 3 segundos
const int servopin = 5;
int ang = 0; 
bool falloMostrado = false; 


void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  dht.begin();
  pinMode(trigpin, OUTPUT);
  pinMode(echopin, INPUT);
  delay(2000); // Esperar al sensor DHT11
  myservo.attach(servopin);
  myservo.write(0);

}

void loop() {

  // 1. Comprobar si llega un comando desde la estación   
  if (mySerial.available()) {
    Serial.println ("he recibido");
    String mensaje = mySerial.readStringUntil('\n');
    mensaje.trim();

    if (mensaje == "Iniciar") {
      enviarDatos = true;
      Serial.println("Orden recibida: Iniciar");
    }

    else if (mensaje == "Parar") {
      enviarDatos = false;
      Serial.println("Orden recibida: Parar");

    }
    else if (mensaje == "Reanudar") {
      enviarDatos = true;
      Serial.println("Orden recibida: Reanudar");
    }

  }
  //  Enviar datos cada 3 segundos si enviarDatos = true
  unsigned long ahora = millis();
 if (enviarDatos) {
    ultimoEnvio = ahora;
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (isnan(h) || isnan(t)) {  
      if (!esperandoTimeout) {
        Serial.println("Error: no se reciben datos del DHT11");
        esperandoTimeout = true;
        nextTimeoutHT = ahora + 5000;
      }
    }else{
esperandoTimeout = false;
      mySerial.print("T:");
      mySerial.print(t);
      mySerial.print(":H:");
      mySerial.print(h);
      mySerial.print(":D:");
      mySerial.print(dist);
      mySerial.print(":A:");
      mySerial.print(ang);
      Serial.println(t);
  delay(3000);

}
if (esperandoTimeout && (ahora >= nextTimeoutHT)) {
    esperandoTimeout = false;
      if (!falloMostrado) {
        Serial.println("FALLO");
        mySerial.print("FALLO");
        falloMostrado = true;
    }

  }
    digitalWrite(trigpin, LOW);
    delayMicroseconds(2);
    digitalWrite(trigpin, HIGH);
    delayMicroseconds(10);
    digitalWrite(trigpin, LOW);
    duracion=pulseIn(echopin, HIGH);
    dist=(duracion*.0343)/2;
    for (ang = 0; ang <= 180; ang += 1) { // goes from 0 degrees to 180 degrees
    // in steps of 1 degree
    myservo.write(ang);              // tell servo to go to position in variable 'pos'
    delay(15);          

              // waits 15 ms for the servo to reach the position

  }
  for (ang = 180; ang >= 0; ang -= 1) { // goes from 180 degrees to 0 degrees
    myservo.write(ang);  
              // tell servo to go to position in variable 'pos'
    delay(15);                       // waits 15 ms for the servo to reach the position
  }
 }
}