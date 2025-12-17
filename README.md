👥 Grupo 13


 	Sebastián Simó



 	Violeta López



 	Eric Galán



🛰️ Proyecto Satélite Arduino



Este proyecto consiste en un sistema satelital basado en Arduino capaz de enviar datos en tiempo real a una estación tierra.



 El satélite incluye:



 	🌡️ Sensor de temperatura y humedad





 	📡 Radar para mapeo básico de proximidad, que se puede utilizar automáticamente o manualmente mediante un joystick





 	🌌 Sistema de comunicación de su posición en el espacio





 	📊 Visualización en una interfaz de Python con gráficos seleccionables por el usuario



🧰 Funcionalidades destacadas

	Implementación de un joystick para controlar el radar manualmente.

	Implementación de una órbita en 3D en la interfaz gráfica, facilitando la posición y trayectoria del satélite

	Implementación de un grountrack que muestra la proyección del recorrido del satélite sobre la superfície terrestre.

	Uso de comunicaciones más ligeras y eficientes para optimizar el envío de datos entre satélite y estación tierra.


🎥 Videos del Proyecto



 	Versión 1 – https://youtu.be/cQfJn75w86E





 	Versión 2 –  https://youtu.be/2Swc2H1iLk4





 	Versión 3 – https://youtu.be/LPQKkWT3guA





 	Versión Final – https://youtu.be/XS9eTHN4k6E







📝 Descripción General



El satélite recoge datos ambientales y de proximidad mediante sus sensores. Toda esta información se envía mediante comunicación inalámbrica hacia la estación tierra, que la procesa y la reenvía a una interfaz creada en Python.





La interfaz permite:



 	Elegir qué gráfico visualizar, este puede ser de temperatura, de humedad, el radar, las medias de las temperaturas por un lado y el groundtrack o una órbita en 3D por otro.





 	Analizar temperatura, humedad, proximidad, posición y eventos registrados.





 	Ver datos en tiempo real o cargados previamente.


📨Protocolo de Aplicación:



T:...:H:...:D:...:A:...    → Datos de Temperatura (T), Humedad (H), Distancia ultrasónica (D) y Ángulo del servo (A)

FALLO                      → Fallo en sensor DHT11 (temperatura/humedad)

DIST                       → Fallo en sensor ultrasónico (no se reciben datos)

COMMS                      → Error en comunicaciones del satélite

Barrido                    → Servo en barrido automático

Manual                     → Servo en modo manual

AlarmaLimiteOn             → Alarma de temperatura media sobrepasada activada

AlarmaLimiteOff            → Alarma de temperatura media sobrepasada desactivada

Iniciar                    → Iniciar envío de datos

Parar                      → Detener envío de datos

Reanudar                   → Reanudar envío de datos

Medias                     → Satélite calcula medias de temperatura

MediaStop                  → Detener cálculo de medias en satélite

PERIODO:<valor>            → Cambiar periodo de envío de datos (milisegundos)

SumaAngulo15               → Sumar 15° al ángulo del servo

RestaAngulo15              → Restar 15° al ángulo del servo

BotonPulsado               → Activar/desactivar modo manual del servo

P: (X:... Y:... Z:...)     → Posición 3D de la órbita del satélite







🔌Conexiones:





