import tkinter as tk
from tkinter import messagebox, simpledialog
import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from matplotlib.animation import FuncAnimation

#Configuración del puerto serie
device = 'COM5'  # Cambia si es necesario
mySerial = serial.Serial(device, 9600, timeout=1)

#Definición de variables
temperaturas = []
eje_x = []
i = 0
running = False  # Estado de lectura
mostrar_radar = False  # Estado del gráfico mostrado
mostrar_medias = False #Estado del gráfico mostrado
NUM_MUESTRAS = 10
indice = 0
z = 0
sumaT = 0
contador = 0
limite = 0

#Definimos la función de la recepción de los datos del arduino satélite
def recepcion():
    global i, running, distancia, angulo
    while running:
        try:
            if mySerial.in_waiting > 0:
                linea_recibida = mySerial.readline().decode('utf-8').rstrip()
                print(linea_recibida)
                if linea_recibida.startswith("T:"):
                    trozos = linea_recibida.split(':')
                    temperatura = float(trozos[1])
                    distancia = float(trozos[5])
                    angulo = float(trozos[7])
                    eje_x.append(i)
                    temperaturas.append(temperatura)
                    i += 1
                if not mostrar_radar:
                    root.after(0, actualizar_grafica_gui)

        except Exception as e:
            print("Error (tierra):", e)


#GRÁFICA DE TEMPERATURA
def actualizar_grafica_gui():
    ax_temp.clear()
    ax_temp.set_xlim(0, max(20, len(eje_x)))
    ax_temp.set_ylim(0, 50)
    ax_temp.plot(eje_x, temperaturas, marker='o', linestyle='-')
    ax_temp.set_title('Temperatura en tiempo real')
    ax_temp.set_xlabel('Muestras')
    ax_temp.set_ylabel('Temperatura (°C)')
    canvas_temp.draw()

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

#Definimos los botones para el cambio de gráfico
def mostrar_grafico_temp():
    global mostrar_radar, mostrar_medias
    mostrar_radar = False
    mostrar_medias = False
    grafica_frame.tkraise() 

def mostrar_grafico_radar():
    global mostrar_radar
    mostrar_radar = True
    mostrar_grafico_medias = False
    radar_frame.tkraise()
    canvas_radar.draw()
def mostrar_grafico_medias():
    global mostrar_radar, mostrar_medias
    mostrar_radar = False
    mostrar_medias = True
    medias_frame.tkraise()

def cambiar_periodo():
    nuevo = simpledialog.askinteger(
        "Periodo de transimisón",
        "Introduce el nuevo periodo de transimisión en milisegundos:",
        minvalue = 100
    )
    if nuevo is not None:
        comando = "PERIODO:{}\n".format(nuevo) # usamos format para que se escriba el número
        mySerial.write(comando.encode())
        messagebox.showinfo("Periodo actualizado", f"Nuevo periodo: {nuevo} ms")
def medias_satelite():
    linea_recibida = mySerial.readline().decode('utf-8').rstrip()
    mySerial.write(b'Medias\n')
    trossos2 = linea_recibida.split(":")
    mediaT = trossos2[9]
    if (mediaT >= limite and contador != 3):
        contador = contador + 1
    if (contador == 3):
        mySerial.write(b'Limite')
    if (mediaT < limite):
        contador = 0
        mySerial.write(b'Nolimite')


def limite_usu():
    try:
        limite = simpledialog.askinteger(
            "Limite de medias",
            "Introduce el nuevo limite de temperaturas:",
            minvalue = 0,
            maxvalue = 30
        )
        if limite is not None:
            # comando = "LIMITE:{}\n".format(limite)
            # mySerial.write(comando.encode())
            messagebox.showinfo(f"Nuevo limite: {limite} ºC")
    except Exception as e2:
        print("Error (limite):", e2)
    '''try:
        entry_num = tk.Entry(root)
        limite = int(entry_num.get())
    except ValueError:
        print("Por favor, escribe un número válido")'''


def medias_tierra():
    linea_recibida = mySerial.readline().decode('utf-8').rstrip()
    trossos = linea_recibida.split(":")
    mySerial.write(b'MediaStop\n') # para que deje de calcular medias el satelite
    #temperaturas[NUM_MUESTRAS]
    mediaT=[]
    sumaT == 0
    '''while (indice < NUM_MUESTRAS):
        temperaturas[indice] = trossos[1]
        indice = indice + 1'''
    
    if (indice == NUM_MUESTRAS):
        while (z<NUM_MUESTRAS):
            sumaT = sumaT + temperaturas[z]
            z = z + 1
        
        mediaT.append(sumaT/NUM_MUESTRAS)
        print(str(mediaT[len(mediaT)-1])) # Para que muestre en consola la ultima media tierra.
        
        if (mediaT[indice] >= limite and contador != 3):
            contador = contador + 1
        if (contador == 3):
            mySerial.write(b'Limite')
        if (mediaT[indice] < limite):
            contador = 0
            mySerial.write(b'Nolimite')

        # temperaturas.pop(0)
        z = 0
        # temperaturas.append(trossos[1])



#CÓDIGO INTERFAZ GRÁFICA
root = tk.Tk()
root.geometry("1400x650")
root.title("Interfaz con Temperatura y Radar Ultrasónico")

for c in range(3):
    root.columnconfigure(c, weight=1)
for r in range(4):
    root.rowconfigure(r, weight=1)

#Definimos el botón iniciar
button_iniciar_frame = tk.LabelFrame(root, text="Iniciar")
button_iniciar_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
button_iniciar_frame.rowconfigure(0, weight=1)
button_iniciar_frame.columnconfigure(0, weight=1)
tk.Button(button_iniciar_frame, text="Iniciar", bg="red", fg="white", command=iniciar).grid(sticky="nsew")

#Definimos el botón parar
button_parar_frame = tk.LabelFrame(root, text="Parar")
button_parar_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
button_parar_frame.rowconfigure(0, weight=1)
button_parar_frame.columnconfigure(0, weight=1)
tk.Button(button_parar_frame, text="Parar", bg="blue", fg="white", command=parar).grid(sticky="nsew")

#Definimos el botón reanudar
button_reanudar_frame = tk.LabelFrame(root, text="Reanudar")
button_reanudar_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
button_reanudar_frame.rowconfigure(0, weight=1)
button_reanudar_frame.columnconfigure(0, weight=1)
tk.Button(button_reanudar_frame, text="Reanudar", bg="white", fg="black", command=reanudar).grid(sticky="nsew")

#Definimos el botón de cambiar de periodo
button_periodo_frame = tk.LabelFrame(root, text="Cambiar periodo")
button_periodo_frame.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")
button_periodo_frame.rowconfigure(0, weight=1)
button_periodo_frame.columnconfigure(0, weight=1)
tk.Button(button_periodo_frame, text="Cambiar periodo", bg="orange", fg="black", command=cambiar_periodo).grid(sticky="nsew")


#Definimos los botones para cambiar de gráfica
button_selector_frame = tk.LabelFrame(root, text="Seleccionar gráfico")
button_selector_frame.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")
button_selector_frame.rowconfigure(0, weight=1)
button_selector_frame.columnconfigure(0, weight=1)
tk.Button(button_selector_frame, text="Ver medias temperatura", bg="lightgreen", command=mostrar_grafico_temp).grid(sticky="ew", padx=5, pady=3)
tk.Button(button_selector_frame, text="Ver Radar", bg="lightblue", command=mostrar_grafico_radar).grid(sticky="ew", padx=5, pady=3)
tk.Button(button_selector_frame, text="Ver gráfica temperatura", bg="cyan", command=mostrar_grafico_medias).grid(sticky="ew", padx=5, pady=3)

#Definimos el botón decidir donde calcular las medias
button_selector2_frame = tk.LabelFrame(root, text="Seleccionar donde hacer las medias.")
button_selector2_frame.grid(row=4, column=1, padx=5, pady=5, sticky="nsew")
button_selector2_frame.rowconfigure(0, weight=1)
button_selector2_frame.columnconfigure(0, weight=1)
tk.Button(button_selector2_frame, text="En satélite", bg="orange", command=medias_satelite).grid(sticky="ew", padx=5, pady=3)
tk.Button(button_selector2_frame, text="En tierra", bg="green", command=medias_tierra).grid(sticky="ew", padx=5, pady=3)

#Definimos el botón límite de temperatura
button_limite_frame = tk.LabelFrame(root, text="Limite medias" )
button_limite_frame.grid(row=6, column=0, padx=5, pady=5, sticky="nsew")
button_limite_frame.rowconfigure(0, weight=1)
button_limite_frame.columnconfigure(0, weight=1)
tk.Button(button_iniciar_frame, text="Limite medias", bg="white", fg="black", command=limite_usu).grid(sticky="nsew")

#Frame de la gráfica de las medias de la temperatura
grafica_frame = tk.LabelFrame(root, text="Gráfica de medias Temperatura")
grafica_frame.grid(row=0, column=1, rowspan=4, padx=5, pady=5, sticky="nsew")
grafica_frame.columnconfigure(0, weight=1)
grafica_frame.rowconfigure(0, weight=1)

#Creamos los canvas para que aparezca la gráfica
fig_temp, ax_temp = plt.subplots(figsize=(6, 4))
canvas_temp = FigureCanvasTkAgg(fig_temp, master=grafica_frame)
canvas_temp.draw()
canvas_temp.get_tk_widget().grid(row=0, column=0, sticky="nsew")

#Frame del radar
radar_frame = tk.LabelFrame(root, text="Radar Ultrasónico")
radar_frame.grid(row=0, column=1, rowspan=4, padx=5, pady=5, sticky="nsew")
radar_frame.columnconfigure(0, weight=1)
radar_frame.rowconfigure(0, weight=1)

fig_radar = plt.Figure(figsize=(6, 4))
ax_radar = fig_radar.add_subplot(111, polar=True)
ax_radar.set_title("Radar Ultrasónico", va='bottom')
ax_radar.set_rlim(0, 250)
ax_radar.set_thetamin(0)
ax_radar.set_thetamax(180)
ax_radar.set_theta_zero_location('E')
ax_radar.set_theta_direction(1)
ax_radar.set_rlabel_position(0)

linea, = ax_radar.plot([], [], color='green', linewidth=2)
punto, = ax_radar.plot([], [], 'go', markersize=8)
texto = ax_radar.text(np.deg2rad(90), 52, "", ha='center', va='center', fontsize=10, color='black')

#Creamos los canvas para que aparezca la gráfica
canvas_radar = FigureCanvasTkAgg(fig_radar, master=radar_frame)
canvas_radar.draw()
canvas_radar.get_tk_widget().grid(row=0, column=0, sticky="nsew")

#Frame gráfica de temperatura
medias_frame = tk.LabelFrame(root, text = "Gráfica de temperatura")
medias_frame.grid(row=0, column=1, rowspan=4, padx=5, pady=5, sticky="nsew")
medias_frame.columnconfigure(0, weight=1)
medias_frame.rowconfigure(0, weight=1)
#Creamos los canvias para que se dibuje la gráfica de las medias
fig_temp, ax_temp = plt.subplots(figsize=(6, 4))
canvas_temp = FigureCanvasTkAgg(fig_temp, master=medias_frame)
canvas_temp.draw()
canvas_temp.get_tk_widget().grid(row=0, column=0, sticky="nsew")

#Animación del radar
def animar_radar(frame):
    global angulo, distancia
    theta = np.deg2rad(angulo)
    linea.set_data([theta, theta], [0, distancia])
    punto.set_data([theta], [distancia])
    texto.set_text(f"Ángulo: {angulo}° | Distancia: {distancia:.1f} cm")
    return linea, punto, texto
angulo = 0
distancia = 0
ani = FuncAnimation(fig_radar, animar_radar, interval=50, blit=False, cache_frame_data=False)

#Mostrar solo temperatura al inicio
radar_frame.lower()

#Funciones para alternar gráficos
def mostrar_grafico_temp():
    global mostrar_radar
    mostrar_radar = False
    grafica_frame.tkraise()
    canvas_temp.draw()  

def mostrar_grafico_radar():
    global mostrar_radar
    mostrar_radar = True
    radar_frame.tkraise()
    canvas_radar.draw() 

#Ejecutar interfaz
root.mainloop()