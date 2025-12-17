int mov_X;
int mov_Y;
int SW;
const int pulsador=8;
unsigned long lastEnvioJoystick=0;
unsigned long tiempoJoystick=3000; // Tiempo entre envios del joystick

void setup() {
  pinMode(pulsador, INPUT_PULLUP);
  lastEnvioJoystick=millis();
  Serial.begin(9600);
}

void loop() {

  mov_X=analogRead(A0);
  mov_Y=analogRead(A1);
  SW=digitalRead(pulsador);

  if(millis()>=lastEnvioJoystick+tiempoJoystick){

    if(mov_X>=768){
      Serial.println("SumaAngulo15");
    }

    if(mov_X<=255){
      Serial.println("RestaAngulo15");
    }

    if(!SW){
      Serial.println("BotonPulsado");
    }

    lastEnvioJoystick=millis();

  }

}