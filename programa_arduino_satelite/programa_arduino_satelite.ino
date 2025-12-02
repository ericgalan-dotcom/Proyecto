#include <SoftwareSerial.h>
#include <DHT.h>
#include <Servo.h>

#define DHTPIN 2
#define DHTTYPE DHT11

Servo myservo;
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11);

//Definimos las variables
const int trigpin=8;
const int echopin=7;
const int servopin = 5;

float duracion, dist;
float h, t;

bool esperandoTimeout = false;
bool enviarDatos = false;
bool falloMostrado = false;
bool media_satelite = false;

const int NUM_MUESTRAS = 10;
float temperaturas[NUM_MUESTRAS];
int indice = 0;

int ang = 0; 
unsigned long periodoTH = 5000;       // Periodo configurable desde Python
unsigned long nextEnvioTH = 0;        // Controla la frecuencia de envío
unsigned long nextTimeoutHT = 0;
unsigned long ultimoEnvio = 0;

//VARIABLES PARA LA SIMULACIÓN DE LA ÓRBITA
const double G = 6.67430e-11;  // Gravitational constant (m^3 kg^-1 s^-2)
const double M = 5.97219e24;   // Mass of Earth (kg)
const double R_EARTH = 6371000;  // Radius of Earth (meters)
const double ALTITUDE = 400000;  // Altitude of satellite above Earth's surface (meters)
const double EARTH_ROTATION_RATE = 7.2921159e-5;  // Earth's rotational rate (radians/second)
const unsigned long MILLIS_BETWEEN_UPDATES = 1000; // Time in milliseconds between each orbit simulation update
const double  TIME_COMPRESSION = 90.0; // Time compression factor (90x)

// Variables
unsigned long nextUpdate; // Time in milliseconds when the next orbit simulation update should occur
double real_orbital_period;  // Real orbital period of the satellite (seconds)
double r;  // Total distance from Earth's center to satellite (meters)

char check[64] = "";
char buffer[50];

//Funciones
void procesarComando() { //Leemos todos los mensajes que se envian des del python y según lo que recibimos hacemos una acción o otra. 
 // 1. Comprobar si llega un comando desde la estación   
  if (mySerial.available()) {
    Serial.println ("he recibido");
    String mensaje = mySerial.readStringUntil('\n');
    mensaje.trim();

  Serial.print("Comando recibido: ");
  Serial.println(mensaje);

  if (mensaje == "Iniciar") {
    enviarDatos = true;
  }
  else if (mensaje == "Parar") {
    enviarDatos = false;
  }
  else if (mensaje == "Reanudar") {
    enviarDatos = true;
  }
  else if (mensaje == "Medias") {
    media_satelite = true;
    indice = 0;
  }
  else if (mensaje=="MediaStop"){
    media_satelite=false;
  }
  else if (mensaje.startsWith("PERIODO:")) {
    unsigned long nuevoPeriodo = mensaje.substring(8).toInt();
    if (nuevoPeriodo > 0) {
      periodoTH = nuevoPeriodo;
      Serial.print("Nuevo periodoTH: ");
      Serial.println(periodoTH);
    }
  }
}
}
void medirUltrasonidos() { //Controla el sensor ultrasónico

  digitalWrite(trigpin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigpin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigpin, LOW);

  duracion = pulseIn(echopin, HIGH, 30000);
  dist = (duracion * 0.0343) / 2;
}


void medirTemperaturaHumedad() { //Funcionammiento del sensor de temperatura y humedad.

  h = dht.readHumidity();
  t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    if (!esperandoTimeout) {                    //Este paso de aquí es para detectar errores en la transimisón de datos, si el sensor falla activa el esperandoTimeout y programa
      esperandoTimeout = true;                  // otro timeout de 5s. 
      nextTimeoutHT = millis() + 5000;
      Serial.println("Error: no se reciben datos del DHT11");
    }
  } else {
    esperandoTimeout = false;
    falloMostrado = false;
    nextEnvioTH = millis() + periodoTH; 
  }

}


void verificarTimeout() {

  if (millis() >= nextTimeoutHT) {
    esperandoTimeout = false;           //Esta función es para activar la alarma, si han pasado 5s desde el primer error del sensor envía "FALLO" para que se active la alarma.
    if (!falloMostrado) {
      falloMostrado = true;
      Serial.println("FALLO");
      mySerial.println("FALLO");
    }
  }

}

void barridoServo() {

  // Barrido 0° a 180°
  for (ang = 0; ang <= 180; ang += 15) {
    procesarComando();
    if (enviarDatos){
      myservo.write(ang);
      if (esperandoTimeout) {
      verificarTimeout();
    } 
      else if (millis() >= nextEnvioTH) {
      medirUltrasonidos();
      medirTemperaturaHumedad();
      if (!esperandoTimeout) {
        enviarDatosMedidos(t,h,dist,ang);
      }
    }
    delay(50);
    }
    
  }

  // Barrido 180° a 0°
 for (ang = 180; ang >= 0; ang -= 15) {
    procesarComando();
    if (enviarDatos){
       myservo.write(ang);
    if (esperandoTimeout) {
      verificarTimeout();
    } 
    else if (millis() >= nextEnvioTH) {
      medirUltrasonidos();
      medirTemperaturaHumedad();
      if (!esperandoTimeout) {
        enviarDatosMedidos(t,h,dist,ang);
      }
    }
    delay(50);
    }
   
    
 }

 }


void enviarDatosMedidos(float t, float h, float dist, int ang) { //Esta funcón se encarga de enviar los datos con el código estipulado para que el python lo lea y se genera la gráfica.

  mySerial.print("T:");
  mySerial.print(t);
  mySerial.print(":H:");
  mySerial.print(h);
  mySerial.print(":D:");
  mySerial.print(dist);
  mySerial.print(":A:");
  mySerial.print(ang);
  //CHEKSUM
  strcat(check, "T");
  sprintf(buffer, "%d", t);
  strcat(check, buffer);

  strcat(check, "H");
  sprintf(buffer, "%d", h);
  strcat(check, buffer);

  strcat(check, "D");
  sprintf(buffer, "%d", dist);
  strcat(check, buffer);

  strcat(check, "A");
  sprintf(buffer, "%d", ang);
  strcat(check, buffer);



  unsigned int checksum = 0;
  for (int q = 0; check[q] != '\0'; q++) {
    checksum += (unsigned char)check[q];
  }
  checksum %= 256;
  mySerial.print(":");
  mySerial.println(checksum);
  Serial.print(t);
  Serial.println(checksum);
  delay(50);



  if (media_satelite) {       //Además se calcula la media cada diez datos de temperatura. 
    temperaturas[indice] = t;
    indice++;
    if (indice == NUM_MUESTRAS) {
      float sumaT = 0;
      for (int i = 0; i < NUM_MUESTRAS; i++) sumaT += temperaturas[i]; 
      float mediaT = sumaT / NUM_MUESTRAS;
      mySerial.print(":M:"); // CAMBIAR EN EL PYTHON EL TROZO QUE ESPERA (espera ":Media Temperaturas:")
      mySerial.print(mediaT);
      indice = 0;
    }
  }

  mySerial.println(); // Envia final de línea // Verificar con el kit si hace falta

}


void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  dht.begin();
  pinMode(trigpin, OUTPUT);
  pinMode(echopin, INPUT);
  myservo.attach(servopin);
  myservo.write(0);
  delay(2000); // Esperar al sensor DHT11
  nextEnvioTH = millis() + periodoTH; 
  nextUpdate = MILLIS_BETWEEN_UPDATES;
    
  r = R_EARTH + ALTITUDE;
  real_orbital_period = 2 * PI * sqrt(pow(r, 3) / (G * M));
}

void loop() {
  procesarComando();
  barridoServo();
   
 }