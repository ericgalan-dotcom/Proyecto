import serial
import matplotlib.pyplot as plt
import threading
device = 'COM5'
mySerial = serial.Serial(device, 9600)
plt.ion()
plt.axis([0,20,15,30])
temperaturas=[]
eje_x=[]
i=0

# 

from tkinter import *
def recepcion ():
    while True:
        if mySerial.in_waiting > 0:
            line = mySerial.readline().decode('utf-8').rstrip()
            print(line)
            trozos=line.split(':')
            eje_x.append(i)
            temperatura=float(trozos[1])
            temperaturas.append(temperatura)
            plt.plot(eje_x,temperaturas)
            plt.title(str(i))
            i=i+1
            plt.draw()
            plt.pause(0.5)
# line,=eje_x.plot([],[],'r-') # Línea que marca temperaturas     

def AClick ():
    mensaje = "Iniciar\n"
    mySerial.write(mensaje.encode('utf-8'))
    threadRecepcion = threading.Thread (target = recepcion)
    threadRecepcion.start()

def BClick ():
    mensaje = "Parar\n"
    mySerial.write(mensaje.encode('utf-8'))
    

def CClick ():
    mensaje = "Reanudar\n"
    mySerial.write(mensaje.encode('utf-8'))


window = Tk()
window.geometry("400x400")
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=1)
window.rowconfigure(2, weight=1)
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.columnconfigure(2, weight=1)
window.columnconfigure(3, weight=1)

AButton = Button(window, text="Iniciar", bg='red', fg="white",command=AClick)
AButton.grid(row=2, column=0, padx=5, pady=5, sticky=N + S + E + W)

BButton = Button(window, text="Parar", bg='white', fg="black",command=BClick)
BButton.grid(row=2, column=1, padx=5, pady=5, sticky=N + S + E + W)

CButton = Button(window, text="Reanudar", bg='blue', fg="white",command=CClick)
CButton.grid(row=2, column=2, padx=5, pady=5, sticky=N + S + E + W)

window.mainloop()
