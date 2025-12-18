# 🛰️ Proyecto Satélite Arduino

👥 Grupo 13

* Sebastián Simó
* Violeta López
* Eric Galán



📡 Descripción del Proyecto

Este proyecto consiste en un sistema satelital basado en **Arduino**, capaz de enviar datos en **tiempo real** a una **estación tierra**, donde se procesan y visualizan mediante una interfaz en Python.



🧩 Componentes del Satélite

* 🌡️ Sensor de temperatura y humedad
* 📡 Radar de proximidad, operable en modo automático o manual mediante joystick
* 🌌 Sistema de comunicación de la posición en el espacio
* 📊 Interfaz gráfica en Python con gráficos seleccionables por el usuario



🧰 Funcionalidades Destacadas

* Control manual del radar mediante joystick
* Representación de una órbita 3D en la interfaz gráfica
* Visualización del groundtrack, mostrando la proyección del recorrido del satélite sobre la superficie terrestre
* Uso de comunicaciones más ligeras y eficientes para optimizar el envío de datos entre satélite y estación tierra


🎥 Videos del Proyecto

* Versión 1 → https://youtu.be/cQfJn75w86E
* Versión 2 → https://youtu.be/2Swc2H1iLk4
* Versión 3 → https://youtu.be/LPQKkWT3guA
* Versión Final → https://youtu.be/XS9eTHN4k6E



📝 Descripción General

El satélite recoge datos ambientales y de proximidad mediante sus sensores. Esta información se envía de forma inalámbrica a la estación tierra, donde se procesa y se visualiza en una interfaz desarrollada en Python.

La interfaz permite:

* Seleccionar distintos gráficos: temperatura, humedad, radar, medias de temperatura, groundtrack y órbita 3D
* Analizar temperatura, humedad, proximidad, posición y eventos registrados
* Visualizar datos en tiempo real o cargar datos previamente almacenados


📨 Protocolo de Aplicación

```
T:...:H:...:D:...:A:...    → Temperatura (T), Humedad (H), Distancia (D) y Ángulo del servo (A)
FALLO                      → Error en sensor DHT11
DIST                       → Error en sensor ultrasónico
COMMS                      → Error en comunicaciones
Barrido                    → Servo en barrido automático
Manual                     → Servo en modo manual
AlarmaLimiteOn             → Alarma de temperatura media activada
AlarmaLimiteOff            → Alarma de temperatura media desactivada
Iniciar                    → Iniciar envío de datos
Parar                      → Detener envío de datos
Reanudar                   → Reanudar envío de datos
Medias                     → Cálculo de medias de temperatura
MediaStop                  → Detener cálculo de medias
PERIODO:<valor>            → Cambiar periodo de envío (ms)
SumaAngulo15               → Incrementar ángulo del servo en 15°
RestaAngulo15              → Reducir ángulo del servo en 15°
BotonPulsado               → Activar/desactivar modo manual
P: (X:... Y:... Z:...)     → Posición 3D del satélite


🔌 Conexiones
