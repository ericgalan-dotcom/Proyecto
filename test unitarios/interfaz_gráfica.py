import tkinter as tk
from tkinter import messagebox
import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#Configuración del puerto serie
device = 'COM5'  # Cambiar si es necesario
mySerial = serial.Serial(device, 9600, timeout=1)


#Definición de variables
temperaturas = []
eje_x = []
i = 0
running = False  # Estado de lectura

#Definimos la función de la recepción de los datos del arduino satélite
def recepcion():
    global i, running
    while running:
        try:
            if mySerial.in_waiting > 0:
                linea = mySerial.readline().decode('utf-8').rstrip()
                print(linea)
                trozos = linea.split(':')
                temperatura = float(trozos[1])
                eje_x.append(i)
                temperaturas.append(temperatura)
                i=i+1
                plt.draw()
                i += 1
                actualizar_grafica()
        except Exception as e:
            print("Error (tierra):", e)

# Actualizamos la gráfica
def actualizar_grafica():
    ax.clear()
    ax.set_xlim(0, max(100, len(eje_x)))
    ax.set_ylim(0, 30)
    ax.plot(eje_x, temperaturas, color='blue', marker='o', linestyle='-')
    ax.set_title('Temperatura en tiempo real')
    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Temperatura (°C)')
    canvas.draw()

#Definimos las diferentes funciones de los botones: Iniciar, Parar y Reanudar
def iniciar():
    global running
    if not running:
        running = True
        mySerial.write(b'Iniciar\n')
        threading.Thread(target=recepcion, daemon=True).start()

def parar():
    global running
    running = False
    mySerial.write(b'Parar\n')
    messagebox.showinfo("Info", "Lectura detenida")

def reanudar():
    global running
    if not running:
        running = True
        mySerial.write(b'Reanudar\n')
        threading.Thread(target=recepcion, daemon=True).start()
        messagebox.showinfo("Info", "Lectura reanudada")

#Código de la interfaz gráfica
root = tk.Tk()
root.geometry("900x500")
root.title("Interfaz Gráfica con Lectura de Temperatura")

root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=10)
for r in range(3):
    root.rowconfigure(r, weight=1)

#Definimos el botón iniciar
button_iniciar_frame= tk.LabelFrame(root, text="Iniciar")
button_iniciar_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
button_iniciar_frame.rowconfigure(0, weight=1)
button_iniciar_frame.columnconfigure(0, weight=1)
tk.Button(button_iniciar_frame, text="Iniciar", bg="red", fg="white", command=iniciar).grid(row=0, column=0, sticky="nsew")

#Definimos el botón parar
button_parar_frame = tk.LabelFrame(root, text="Parar")
button_parar_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
button_parar_frame.rowconfigure(0, weight=1)
button_parar_frame.columnconfigure(0, weight=1)
tk.Button(button_parar_frame, text="Parar", bg="blue", fg="white", command=parar).grid(row=0, column=0, sticky="nsew")

#Definimos el botón reanudar
button_reanudar_frame = tk.LabelFrame(root, text="Reanudar")
button_reanudar_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
button_reanudar_frame.rowconfigure(0, weight=1)
button_reanudar_frame.columnconfigure(0, weight=1)
tk.Button(button_reanudar_frame, text="Reanudar", bg="white", fg="black", command=reanudar).grid(row=0, column=0, sticky="nsew")

#Frame de la gráfica
grafica_frame = tk.LabelFrame(root, text="Gráfica de Temperatura y Humedad")
grafica_frame.grid(row=0, column=1, rowspan=3, padx=5, pady=5, sticky="nsew")
grafica_frame.columnconfigure(index=0, weight=1)
grafica_frame.rowconfigure(index=0, weight = 1)


#Creamos el canvas para que aparezca la gráfica
fig, ax = plt.subplots(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=grafica_frame)
canvas.draw()
canvas.get_tk_widget().pack(fill="both", expand=True)

#Para que nos aparezca la ventana de la interfaz gráfica
root.mainloop()
