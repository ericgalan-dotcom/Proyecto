import serial
device = 'COM3'
mySerial = serial.Serial(device, 9600)
while True:
   if mySerial.in_waiting > 0:
      linea = mySerial.readline().decode('utf-8').rstrip()
      print(linea)