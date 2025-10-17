#include <SoftwareSerial.h>
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11); 

bool enviarDatos = false;
unsigned long ultimoEnvio = 0;
const unsigned long intervalo = 3000;  // cada 3 segundos


void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  dht.begin();
  delay(2000); // Esperar al sensor DHT11
  //Serial.println("Satélite listo.");
 
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
 // if (enviarDatos && (ahora - ultimoEnvio >= intervalo)) {
    ultimoEnvio = ahora;
  // }
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    //if (isnan(h) || isnan(t)) {
      //Serial.println("Error al leer el sensor DHT11"); // Detecta errores
   // } else {
      mySerial.print("T:");
      mySerial.print(t);
      mySerial.print(":H:");
      mySerial.println(h);
    }