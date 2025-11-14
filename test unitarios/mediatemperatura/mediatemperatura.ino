const int NUM_MUESTRAS = 10;
float temperaturas[NUM_MUESTRAS];
int indice = 0;

if (media_satelite){ //ES SOLO PARA HACER LA MEDIA, HACE FALTA PONER EL RESTO
    temperaturas[indice] = t;
    indice++;
  if (indice == NUM_MUESTRAS) {
      float sumaT = 0;
      for (int i = 0; i < NUM_MUESTRAS; i++) {
        sumaT += temperaturas[i];
    }
    float mediaT = sumaT / NUM_MUESTRAS;
    mySerial.print("Media Temperaturas:");
    mySerial.print(mediaT);
