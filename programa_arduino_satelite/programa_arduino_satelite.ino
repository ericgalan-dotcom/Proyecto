// Librerías y definición de variables
#include <SoftwareSerial.h>
#include <DHT.h>
#include <Servo.h>
// Pin del sensor de temperatura y humedad
#define DHTPIN 2
#define DHTTYPE DHT11

Servo myservo;
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11); // Rx: Pin 10, TX: Pin 11

// Pins del sensor de ultrasonidos
const int trigpin=8;
const int echopin=7;
// Pin del servo
const int servopin = 5;
// Variables de temperatura, humedad, y duracion (que luego pasará a distancia)
float duracion, dist;
float h, t;
//  Bools
bool esperandoTimeout = false;
bool enviarDatos = false;
bool falloMostrado = false;
bool media_satelite = false;
bool controlManual=false;
// Variables para las medias de temperatura
const int NUM_MUESTRAS = 10;
float temperaturas[NUM_MUESTRAS];
int indice = 0;
int count_temperaturas = 0;
float suma_temperaturas = 0.0;
float mitjana_temperatura;

int ang = 0;
unsigned long periodoTH = 5000;
unsigned long nextEnvioTH = 0;
unsigned long nextTimeoutHT = 0;
// Variables para la simulación de la órbita
const double G = 6.67430e-11;
const double M = 5.97219e24;
const double R_EARTH = 6371000;
const double ALTITUDE = 400000;
const double EARTH_ROTATION_RATE = 7.2921159e-5;
// Estas dos variables se pueden modificar para que la órbita sea más rápida o más lenta y envie
// los datos a mayor o menor velocidad. Ahora mismo, una órbita dura 5 minutos.
const unsigned long MILLIS_BETWEEN_UPDATES = 5000;
const double  TIME_COMPRESSION = 18.0;

unsigned long nextUpdate;
double real_orbital_period;
double r;
// Función que empaqueta los datos que va a enviar
void packData(float temp, float hum, float dist_cm, int ang_servo, uint8_t tipo_msg, float mitjana, uint8_t* buffer, int* buffer_size) {
  // Comprime la temperatura preservando dos decimales:
    uint16_t t_adj = (uint16_t)constrain((temp - 10.0) * 100.0, 0, 2000);
  // Comprime la humedad preservando dos decimales:
    uint16_t h_adj = (uint16_t)constrain((hum - 50.0) * 100.0, 0, 2000);
  // Comprime la distancia preservando un decimal:
    uint16_t d_adj = (uint16_t)constrain(dist_cm * 10.0, 0, 1000);
  // Finalmente, nos comprime el ángulo del servo
    uint8_t a_adj = (uint8_t)constrain(ang_servo, 0, 180);
  // Empaqueta todo lo anterior en tan solo 6 bytes:
    buffer[0] = (tipo_msg << 5) | ((t_adj >> 7) & 0x1F);
    buffer[1] = t_adj & 0x7F;
    buffer[2] = (h_adj >> 4) & 0xFF;
    buffer[3] = ((h_adj & 0x0F) << 4) | ((d_adj >> 6) & 0x0F);
    buffer[4] = ((d_adj & 0x3F) << 2) | ((a_adj >> 6) & 0x03);
    buffer[5] = (a_adj & 0x3F) << 2;
  // Además, hace lo mismo con la media de temperatura si la tiene que calcular:
    if (tipo_msg == 0x01 && !isnan(mitjana)) {
        uint16_t m_adj = (uint16_t)constrain((mitjana - 10.0) * 100.0, 0, 2000);
        buffer[6] = (m_adj >> 4) & 0xFF;
        buffer[7] = (m_adj & 0x0F) << 4;
        *buffer_size = 8;
    } else {
        *buffer_size = 6;
    }
}

// Función que calcula el checksum con el mensaje ya comprimido
unsigned int calcularChecksumTexto(float t, float h, float dist, int ang, float mitjana) {
    char check[100] = "";
    char bufferNum[20];
    // Convierte el mensaje en un string para calcular el checksum
    strcat(check, "T");
    dtostrf(t, 0, 2, bufferNum);
    strcat(check, bufferNum);
    strcat(check, "H");
    dtostrf(h, 0, 2, bufferNum);
    strcat(check, bufferNum);
    strcat(check, "D");
    dtostrf(dist, 0, 2, bufferNum);
    strcat(check, bufferNum);
    strcat(check, "A");
    sprintf(bufferNum, "%d", ang);
    strcat(check, bufferNum);
    // Hace lo mismo con la media de temperatura si es necesario
    if (!isnan(mitjana)) {
        strcat(check, "M");
        dtostrf(mitjana, 0, 2, bufferNum);
        strcat(check, bufferNum);
    }
    // Finalmente calcula el checksum
    unsigned int checksum = 0;
    for (int i = 0; check[i] != '\0'; i++) {
        checksum += (unsigned char)check[i];
    }
    return checksum % 256;
}

// Una vez tiene datos de temperatura, humedad, etc. envia los datos, ya compactados al arduino 
// tierra, que ya se encargará de descompactarlos.
void enviarDatosMedidosCompactados(float t, float h, float dist, int ang) {
  // Primero calcula la media de temperatura si se lo ha pedido el usuario
    float mitjana_temperatura = NAN;
    uint8_t tipo_msg = 0x00;

    if (media_satelite) {
      if (count_temperaturas == NUM_MUESTRAS) {
        suma_temperaturas -= temperaturas[indice];
      } else {
        count_temperaturas++;
      }

      temperaturas[indice] = t;
      suma_temperaturas += t;

      indice = (indice + 1) % NUM_MUESTRAS;

      mitjana_temperatura = suma_temperaturas / (float)count_temperaturas;

      tipo_msg = 0x01;
    }

    uint8_t paquete[8];  
    int paquete_size = 6;
    // Llama a la función de empaquetado de datos
    packData(t, h, dist, ang, tipo_msg, mitjana_temperatura, paquete, &paquete_size);
    // Calcula el checksum de cada paquete
    unsigned int checksum = 0;
    for (int i = 0; i < paquete_size; i++) {
        checksum += paquete[i];
    }
    checksum = checksum % 256;
    // Envia los paquetes
    for (int i = 0; i < paquete_size; i++) {
        if (paquete[i] < 16) mySerial.print('0');
        mySerial.print(paquete[i], HEX);
    }
    // Al final de todo, escribe el checksum para que se recalcule después en el Python de la estación
    // de tierra
    mySerial.print(':');
    mySerial.println(checksum);
}


// Función que recibe los mensajes que vienen desde la estación de tierra y los interpreta
void procesarComando() {
  if (mySerial.available()) {
    String mensaje = mySerial.readStringUntil('\n');
    mensaje.trim();
    // Inicia, para o reanuda el giro del servo y envio de mensajes
    if (mensaje == "Iniciar") {
      enviarDatos = true;
      media_satelite=false; // Al iniciar el programa, se asume que el usuario no quiere que el satélite calcule medias
    }
    else if (mensaje == "Parar") {
      enviarDatos = false;
    }
    else if (mensaje == "Reanudar") {
      enviarDatos = true;
    }
    // Mensaje para que calcule las medias el satélite
    else if (mensaje == "Medias") {
      media_satelite = true;
    }
    // Mensaje para que las deje de calcular, que se envia cuando las empieza a calcular la estación de tierra
    else if (mensaje=="MediaStop"){
      media_satelite=false;
    }
    // Si el joystick gira a la derecha, gira 15 grados a la derecha.
    else if (mensaje=="SumaAngulo15" && ang!=180){
      ang=ang+15;
      myservo.write(ang);
    }
    // Y viceversa
    else if (mensaje=="RestaAngulo15" && ang!=0){
      ang=ang-15;
      myservo.write(ang);
    }
    // Si el botón (del propio joystick) es pulsado, notifica a tierra de en qué estado se encuentra el control
    // del giro del servo
    else if (mensaje=="BotonPulsado"){
    controlManual=!controlManual; // Si está en automático pasa a manual y viceversa
    if(controlManual){
    mySerial.println("Manual");
    ang=90;
    myservo.write(ang);}
    else{
      mySerial.println("Barrido");
    }
     // Si está en true va a false, si está en false va a true.
  } // Recoge el nuevo periodo de envio de datos de temperatura, humedad y otras variables
    else if (mensaje.startsWith("PERIODO:")) {
      unsigned long nuevoPeriodo = mensaje.substring(8).toInt();
      if (nuevoPeriodo > 0) {
        periodoTH = nuevoPeriodo;
      }
    }
  }
  delay(20);
}
// Función del sensor de ultrasonidos
void medirUltrasonidos() {
  digitalWrite(trigpin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigpin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigpin, LOW);
  duracion = pulseIn(echopin, HIGH, 30000); // Calcula el tiempo entre la salida y la llegada de los ultrasonidos
  dist = (duracion * 0.0343) / 2; // Sabiendo la velocidad del sonido, convierte el tiempo (que es de ida y vuelta)
  // en la distancia (en cm) del sensor al objeto más cercano

  // Se asegura de que se encienda la alarma y el pin verde en tierra si falla este sensor
  if(dist == 0){
    if(!esperandoTimeout){
      esperandoTimeout = true;
      nextTimeoutHT = millis() + 5000;
      Serial.println("Error: no se reciben datos del Sensor ultrasónico");
      mySerial.println("DIST"); 
    }
  }else{
    esperandoTimeout = false;
    falloMostrado = false;
    nextEnvioTH = millis() + periodoTH;
  }
}
// Función del sensor de temperatura y humedad
void medirTemperaturaHumedad() {
  h = dht.readHumidity();
  t = dht.readTemperature();
  // Si por cualquier motivo este sensor falla, deberá activar la alarma y el led rojo.
  if (isnan(h) || isnan(t)) { 
    if (!esperandoTimeout) { // Comienza a contar si hay un fallo
      esperandoTimeout = true;
      nextTimeoutHT = millis() + 5000;
    }
  } else { // Si deja de haber error, ya no notificará del fallo
    esperandoTimeout = false;
    falloMostrado = false;
    nextEnvioTH = millis() + periodoTH;
  }
}
// Si ha habido un error en algún sensor, verifica si han pasado 5 segundos desde que empezó y si es así,
// notifica del fallo.
void verificarTimeout() {
  if (millis() >= nextTimeoutHT) {
    esperandoTimeout = false;
    if (!falloMostrado) {
      falloMostrado = true;
      mySerial.println("FALLO");
    }
  }
}
// Nuestro bucle principal
void barridoServo() {
  if(controlManual){ // Si el control es manual, llama a todas las funciones pero no hace que gire el servo
    procesarComando();
    if (enviarDatos){
      if (esperandoTimeout) {
        verificarTimeout();
      }
      else if (millis() >= nextEnvioTH) {
        medirUltrasonidos();
        medirTemperaturaHumedad();
        if (!esperandoTimeout) {
          enviarDatosMedidosCompactados(t, h, dist, ang);
        }
      }
      delay(20);
    }
  } else { // En cambio, si el control es automático, gira en pasos de 15 grados (y también llama a las funciones)
    for (ang = 0; ang <= 180; ang += 15) {
      procesarComando();
      if (enviarDatos){ // Si no se le dá a iniciar o reanudar, no gira
        myservo.write(ang);
        if (esperandoTimeout) { // Verifica errores
          verificarTimeout();
        }
        else if (millis() >= nextEnvioTH) { // Solo envia si ha pasado el periodo de envio de datos
          medirUltrasonidos();
          medirTemperaturaHumedad();
          if (!esperandoTimeout) {
            enviarDatosMedidosCompactados(t, h, dist, ang); // Envia datos
          }
        }
        delay(20);
      }
    }
    for (ang = 180; ang >= 0; ang -= 15) { // Al llegar al ángulo máximo (180 grados), empieza a girar en la otra dirección
    // Llama a las mismas funciones que en el otro bucle for.
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
            enviarDatosMedidosCompactados(t, h, dist, ang);
          }
        }
        delay(20);
      }
    }
  }
}
// Función que simula la posición del satélite en una órbita ecuatorial
// usando la física (leyes de Kepler y ley de gravitación universal)
void simulate_orbit(unsigned long currentMillis, double inclination, int ecef) {
  // Como vemos, el tiempo actual lo pasa a segundos y aplica la variable TIME_COMPRESSION
  // Esta es la variable que hará que nuestro periodo orbital simulado dure más o menos
    double time = ((double) currentMillis / 1000.0) * TIME_COMPRESSION;
    double angle = 2.0 * PI * (time / real_orbital_period);
    double x = r * cos(angle);
    double y = r * sin(angle) * cos(inclination);
    double z = r * sin(angle) * sin(inclination); // La inclinación es 0, entonces esto siempre dará 0

    if (ecef) {
        double theta = EARTH_ROTATION_RATE * time;
        double x_ecef = x * cos(theta) - y * sin(theta);
        double y_ecef = x * sin(theta) + y * cos(theta);
        x = x_ecef;
        y = y_ecef;
    }

    // Envia los resultados a la estación de tierra
    mySerial.print("ti: ");
    mySerial.print(time);
    mySerial.print(" s | P: (X: ");
    mySerial.print(x);
    mySerial.print(" m, Y: ");
    mySerial.print(y);
    mySerial.print(" m, Z: ");
    mySerial.print(z);
    mySerial.println(" m)");
}
// La función setup, que prepara todo antes de iniciar el programa
void setup() {
  Serial.begin(9600); // Comunicaciones en 9600 baudios
  mySerial.begin(9600);
  dht.begin();
  pinMode(trigpin, OUTPUT);
  pinMode(echopin, INPUT);
  myservo.attach(servopin);
  myservo.write(0);
  delay(2000);
  nextEnvioTH = millis() + periodoTH;
  nextUpdate = MILLIS_BETWEEN_UPDATES;

  r = R_EARTH + ALTITUDE;
  real_orbital_period = 2 * PI * sqrt(pow(r, 3) / (G * M));
}
// La función loop del arduino, que se ejecuta constantemente
void loop() {
  unsigned long currentTime = millis();
  if(currentTime > nextUpdate) {
    simulate_orbit(currentTime, 0, 0);
    nextUpdate = currentTime + MILLIS_BETWEEN_UPDATES;
  }
  procesarComando();
  barridoServo(); // Llama a nuestro loop principal
}