#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11
#define ALARMA_PIN 8   // Pin para LED o buzzer

DHT dht(DHTPIN, DHTTYPE);

unsigned long nextHT = 0;
unsigned long nextTimeoutHT = 0;
bool esperandoTimeout = false;
bool alarmaActiva = false;
bool falloMostrado = false;  // ← NUEVO: evita repetir mensajes

void setup() {
  Serial.begin(9600);
  dht.begin();
  pinMode(ALARMA_PIN, OUTPUT);
  digitalWrite(ALARMA_PIN, LOW);
}

void loop() {
  unsigned long ahora = millis();

  // Leer cada 2 segundos
  if (ahora >= nextHT) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (isnan(h) || isnan(t)) {
      // Solo mostrar "Error" si aún no está activa la alarma
      if (!esperandoTimeout && !alarmaActiva) {
        Serial.println("Error: no se reciben datos del DHT11");
        esperandoTimeout = true;
        nextTimeoutHT = ahora + 5000;  // Esperar 5 s antes de declarar fallo
      }
    } else {
      // ✅ Datos válidos
      Serial.print("T: ");
      Serial.print(t);
      Serial.print(" °C | H: ");
      Serial.print(h);
      Serial.println(" %");

      // Reiniciar todo
      esperandoTimeout = false;
      alarmaActiva = false;
      falloMostrado = false;
      digitalWrite(ALARMA_PIN, LOW); // Apagar alarma
    }

    nextHT = ahora + 2000;  // Próxima lectura en 2 s
  }

  // Si pasaron los 5 s sin datos válidos → activar alarma
  if (esperandoTimeout && (ahora >= nextTimeoutHT)) {
    alarmaActiva = true;
    esperandoTimeout = false;

    // Mostrar "FALLO" una sola vez
    if (!falloMostrado) {
      Serial.println("FALLO: el sensor no responde");
      falloMostrado = true;
    }
  }

  // 🔔 Control de alarma: parpadeo mientras esté activa
  if (alarmaActiva) {
    digitalWrite(ALARMA_PIN, HIGH);
    delay(300);
    digitalWrite(ALARMA_PIN, LOW);}}
  
