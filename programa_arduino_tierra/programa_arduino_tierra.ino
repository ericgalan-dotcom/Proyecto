#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11);

// Variables del joystick

int mov_X;

int mov_Y;

int SW;

const int pulsador = 8;

unsigned long lastEnvioJoystick = 0;

unsigned long tiempoJoystick = 3000;


// Alarma de límite superado

bool alarma_limite = false;

const int ledlimitesuperado = 4;


// Sistema de fallo de ultrasonidos

bool hayFalloUS = false;

bool FalloUSMostrado = false;

const int ledFalloUS = 2;

unsigned long ultimoFalloUS = 0;


// Sistema de alarmas general

const int alarmaPin = 7;

bool alarmaActiva = false;

bool alarmaCommsMostrada = false;

int contadorini = 0;

const int ledfalloDHT = 12;

const int ledfalloComs = 13;


// Timeout de comunicaciones

unsigned long lastReceiveTime = 0;

unsigned long nexttimeout = 0;

unsigned long timeouttime = 10000;


void descomprimirMensaje(String lineaHex) {

  // Verificar formato hex:checksum

  int colonPos = lineaHex.indexOf(':');

  if (colonPos == -1) {

    return;

  }


  String paqueteHex = lineaHex.substring(0, colonPos);

  paqueteHex.trim();

  String checksumStr = lineaHex.substring(colonPos + 1);

  checksumStr.trim();


  // Verificar longitud válida (12 o 16 caracteres = 6 u 8 bytes)

  if (paqueteHex.length() != 12 && paqueteHex.length() != 16) {

    return;

  }


  // Convertir hex a bytes

  uint8_t paquete[8];

  int numBytes = paqueteHex.length() / 2;

 

  for (int i = 0; i < numBytes; i++) {

    String byteStr = paqueteHex.substring(i * 2, i * 2 + 2);

    paquete[i] = (uint8_t)strtol(byteStr.c_str(), NULL, 16);

  }


  // Verificar checksum (suma de bytes mod 256)

  int checksumRecibido = checksumStr.toInt();

  unsigned int checksumCalc = 0;

  for (int i = 0; i < numBytes; i++) {

    checksumCalc += paquete[i];

  }

  checksumCalc = checksumCalc % 256;


  if (checksumCalc != checksumRecibido) {

    Serial.println("Checksum incorrecto, mensaje descartado");

    return;

  }


  // Extraer tipo de mensaje (3 bits más significativos)

  uint8_t tipo_msg = (paquete[0] >> 5) & 0x07;

 

  // Desempaquetar datos bit a bit

  uint16_t t_adj = ((paquete[0] & 0x1F) << 7) | (paquete[1] & 0x7F); // Temperatura: 12 bits

  uint16_t h_adj = (paquete[2] << 4) | ((paquete[3] >> 4) & 0x0F); // Humedad: 12 bits

  uint16_t d_adj = ((paquete[3] & 0x0F) << 6) | ((paquete[4] >> 2) & 0x3F); // Distancia: 10 bits

  uint8_t a_adj = ((paquete[4] & 0x03) << 6) | ((paquete[5] >> 2) & 0x3F); // Ángulo: 8 bits


  // Reconstruir valores reales con offsets

  float temperatura = (t_adj / 100.0) + 10.0;

  float humedad = (h_adj / 100.0) + 50.0;

  float distancia = d_adj / 10.0;

  int angulo = a_adj;


  // Construir mensaje para calcular checksum (sin los ":")

  String mensajeParaChecksum = "T";

  mensajeParaChecksum += String(temperatura, 2);

  mensajeParaChecksum += "H";

  mensajeParaChecksum += String(humedad, 2);

  mensajeParaChecksum += "D";

  mensajeParaChecksum += String(distancia, 2);

  mensajeParaChecksum += "A";

  mensajeParaChecksum += String(angulo);


  // Si hay media (tipo_msg == 1 y 8 bytes)

  if (tipo_msg == 0x01 && numBytes == 8) {

    uint16_t m_adj = (paquete[6] << 4) | ((paquete[7] >> 4) & 0x0F);

    float mitjana = (m_adj / 100.0) + 10.0;

    mensajeParaChecksum += "M";

    mensajeParaChecksum += String(mitjana, 2);

  }


  // Calcular checksum del texto (suma de ASCII mod 256)

  unsigned int checksumTexto = 0;

  for (int i = 0; i < mensajeParaChecksum.length(); i++) {

    checksumTexto += (unsigned char)mensajeParaChecksum.charAt(i);

  }

  checksumTexto = checksumTexto % 256;


  // Construir mensaje descomprimido con formato legible

  String mensajeDescomprimido = "T:";

  mensajeDescomprimido += String(temperatura, 2);

  mensajeDescomprimido += ":H:";

  mensajeDescomprimido += String(humedad, 2);

  mensajeDescomprimido += ":D:";

  mensajeDescomprimido += String(distancia, 2);

  mensajeDescomprimido += ":A:";

  mensajeDescomprimido += String(angulo);


  if (tipo_msg == 0x01 && numBytes == 8) {

    uint16_t m_adj = (paquete[6] << 4) | ((paquete[7] >> 4) & 0x0F);

    float mitjana = (m_adj / 100.0) + 10.0;

    mensajeDescomprimido += ":M:";

    mensajeDescomprimido += String(mitjana, 2);

  }


  mensajeDescomprimido += ":";

  mensajeDescomprimido += String(checksumTexto);


  Serial.println(mensajeDescomprimido);

}


void setup() {

  pinMode(ledfalloDHT, OUTPUT);

  pinMode(ledfalloComs, OUTPUT);

  Serial.begin(9600);

  mySerial.begin(9600);

  pinMode(alarmaPin, OUTPUT);

  digitalWrite(alarmaPin, LOW);

  nexttimeout = millis() + timeouttime;

  pinMode(ledFalloUS, OUTPUT);

  digitalWrite(ledFalloUS, LOW);

  pinMode(pulsador, INPUT_PULLUP);

  lastEnvioJoystick = millis();

}


void loop() {

  // Leer joystick

  mov_X = analogRead(A0);

  mov_Y = analogRead(A1);

  SW = digitalRead(pulsador);


  // Enviar comandos del joystick cada 3 segundos

  if (millis() >= lastEnvioJoystick + tiempoJoystick) {

    if (mov_X >= 768) {

      mySerial.println("SumaAngulo15");

      lastEnvioJoystick = millis();

    }


    if (mov_X <= 255) {

      mySerial.println("RestaAngulo15");

      lastEnvioJoystick = millis();

    }


    if (!SW) {

      mySerial.println("BotonPulsado");

      lastEnvioJoystick = millis();

    }

  }



  if (Serial.available()) {

    String line = Serial.readString();

    mySerial.println(line);

    if (line == "Iniciar\n" || line == "Reanudar\n") {

      contadorini = 1;

    }

    if (line == "Parar\n") {

      contadorini = 0;

    }

    if (line == "AlarmaLimiteOn\n") {

      alarma_limite = true;

    }

    if (line == "AlarmaLimiteOff\n") {

      alarma_limite = false;

    }

  }


  // Gestión de alarmas (solo si está iniciado)

  if (contadorini) {

    // Timeout de comunicaciones (10s sin datos)

    if (millis() >= nexttimeout && !alarmaCommsMostrada) {

      Serial.println("COMMS | Error de comunicación detectado");

      digitalWrite(alarmaPin, HIGH);  

      digitalWrite(ledfalloComs, HIGH);

      alarmaCommsMostrada = true;

    }

    else if (millis() >= nexttimeout && alarmaCommsMostrada) {

      digitalWrite(alarmaPin, HIGH);  

      digitalWrite(ledfalloComs, HIGH);

    }

    else if (millis() < nexttimeout && alarmaCommsMostrada && !hayFalloUS) {

      digitalWrite(ledfalloComs, LOW);

      digitalWrite(alarmaPin, LOW);

      alarmaCommsMostrada = false;

    }

   

    // Alarma de límite superado

    if (alarma_limite) {

      digitalWrite(alarmaPin, HIGH);

      digitalWrite(ledlimitesuperado, HIGH);

    }

    if (!alarma_limite && !hayFalloUS) {

      digitalWrite(alarmaPin, LOW);

      digitalWrite(ledlimitesuperado, LOW);

    }

  }


  if (mySerial.available()) {

    String data = mySerial.readStringUntil('\n');

    data.trim();

    nexttimeout = millis() + timeouttime; // Resetear timeout

   

    // Detectar si es mensaje comprimido (formato hex:checksum)

    bool esMensajeComprimido = false;

    if (data.indexOf(':') != -1 && data.length() >= 13) {

      char primerChar = data.charAt(0);

      if ((primerChar >= '0' && primerChar <= '9') ||

        (primerChar >= 'A' && primerChar <= 'F') ||

        (primerChar >= 'a' && primerChar <= 'f')) {

     esMensajeComprimido = true;

  }

}

   

    if (esMensajeComprimido) {

      descomprimirMensaje(data); // Descomprimir y enviar

    } else {

      Serial.println(data); // Mensajes no comprimidos (FALLO, DIST, etc.)

     

      // Procesar mensajes especiales

      if (data == "FALLO") {

        digitalWrite(alarmaPin, HIGH);

        alarmaActiva = true;

        digitalWrite(ledfalloDHT, HIGH);

      } else if (alarmaActiva && data != "DIST") {

        digitalWrite(alarmaPin, LOW);

        alarmaActiva = false;

        digitalWrite(ledfalloDHT, LOW);

      }


      if (data == "DIST") {

        hayFalloUS = true;

        ultimoFalloUS = millis();

      }

    }

  }


  // Timeout del fallo de ultrasonidos (10s)

  if (millis() > ultimoFalloUS + timeouttime) {

    hayFalloUS = false;

    FalloUSMostrado = false;

  }

 

  if (hayFalloUS && !FalloUSMostrado) {

    digitalWrite(alarmaPin, HIGH);

    digitalWrite(ledFalloUS, HIGH);

    FalloUSMostrado = true;

  }

 

  if (!hayFalloUS) {

    digitalWrite(ledFalloUS, LOW);

  }


  delay(50);

}