import tkinter as tk
from tkinter import messagebox, simpledialog
import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from matplotlib.animation import FuncAnimation
import re   # ORBITA: necesario para la línea de posición
from queue import Queue, Empty
import time
from datetime import datetime
from collections import deque 
from tkinter import ttk  #Importamos el ttk, para el Treeview

#Configuración del puerto serie
device = 'COM5'  # Cambiar si es necesario


#Definición de variables
limite_sobrepasado=False
humedades = []
temperaturas = []
mitjana_temperatures = []
eje_x_medias=[]
eje_x = []
i = 0
running = False  # Estado de lectura
mostrar_temperaturas = True
mostrar_radar = False  # Estado del gráfico mostrado
mostrar_medias = False  
medias_python = False
medias_ard = False
alarma_limite=False
z = 0
sumaT = 0
contador = 0
limite = 0
regex_orbita = re.compile(r"P: \(X: ([\d\.-]+) m, Y: ([\d\.-]+) m, Z: ([\d\.-]+) m\)")

# Colas y sincronización
line_queue = Queue()       
hilo_serial = None         

#Datos para el  dibujo de la órbita
x_vals = []
y_vals = []
z_vals = []


ultimo_update_orbita = 0.0
FPS_ORBITA = 10.0  

#Definición de las variables del radar
angulo = 0
distancia = 0

#Definimos la función de la recepción de los datos del arduino satélite
def recepcion():
    try:
        while running:
            try:
                linea_recibida = mySerial.readline().decode('utf-8').rstrip()
            except Exception:
                linea_recibida = ''
            if linea_recibida:
                line_queue.put(linea_recibida)
    except Exception as e:
        print("Error hilo recepcion:", e)

#Función para procesar la cola de las líneas
def process_serial_queue():
    global i, contador, limite, sumaT, z
    global ultimo_update_orbita, angulo, distancia

    updated_orbit = False

    try:
        for _ in range(50):
            linea_recibida = line_queue.get_nowait()
            print("RX:", linea_recibida)


            if linea_recibida.startswith("T:"):
                try:
                    trozos = linea_recibida.split(':')
                    checksum_recibido = int(trozos[-1])
                    datos = trozos[:-1]
                    mens = "".join(datos)
                    checksum_calculado = 0
                    checksum_calculado = sum(ord(c) for c in mens) % 256
                    print("Checksum calculado: ", checksum_calculado)
                    print("Checksum recibido :",checksum_recibido)
                    if checksum_calculado != checksum_recibido:
                        print("Checksum incorrecto, mensaje descartado")
                    if checksum_calculado == checksum_recibido:
                        temperatura = float(trozos[1])
                        humedad = float(trozos[3])
                        distancia = float(trozos[5]) if len(trozos) > 5 else 0.0
                        angulo = float(trozos[7]) if len(trozos) > 7 else 0.0
                        #Para el cálculo de las medias
                        if medias_python:
                            cua_mitjanes_temperatura = deque(maxlen = 10)
                            cua_mitjanes_temperatura.append(temperatura)
                            mitjana_temperatura = sum(cua_mitjanes_temperatura) / len(cua_mitjanes_temperatura)
                            mitjana_temperatures.append(mitjana_temperatura)
                            eje_x_medias.append(i)
                        if medias_ard:
                            mitjana_temperatura = float(trozos[9])
                            mitjana_temperatures.append(mitjana_temperatura)
                            eje_x_medias.append(i)
                        if not medias_python and not medias_ard:
                            mitjana_temperatures.append(None)
                            #Límite de temperatura
                        if (medias_python or medias_ard) and alarma_limite:
                            if (mitjana_temperatura >= limite) and (contador !=3) :
                                contador = contador + 1
                            if contador >= 3:
                                #Registra la alamra del límite en los eventos
                                mySerial.write(b'AlarmaLimiteOn\n')
                                registrar_evento("ALARMA", "Límite medias")
                                messagebox.showwarning("Alerta", "Las medias de temperatura sobrepasan el límite")
                                if not limite_sobrepasado:
                                    limite_sobrepasado=True
                            if (mitjana_temperatura < limite):
                                contador = 0
                                mySerial.write(b'AlarmaLimiteOff\n')
                                limite_sobrepasado=False
                        eje_x.append(i)
                        temperaturas.append(temperatura)
                        humedades.append(humedad)
                        i += 1
                except Exception as e:
                    print("Error parseando T-line:", e)

            match = regex_orbita.search(linea_recibida)
            if match:
                try:
                    x = float(match.group(1))
                    y = float(match.group(2))
                    z_val = float(match.group(3))

                    x_vals.append(x)
                    y_vals.append(y)
                    z_vals.append(z_val)

                    updated_orbit = True

                except Exception as e:
                    print("Error parseando órbita:", e)
            if linea_recibida.strip() == "FALLO":
                messagebox.showwarning("Satélite", "FALLO en sensor DHT11")
                registrar_evento("ALARMA", "Error del sensor DHT11")
            if linea_recibida.strip() == "DIST":
                messagebox.showwarning("Satélite", "FALLO en sensor de ultrasonidos")
                registrar_evento("ALARMA", "Error del sensor de ultrasonidos")
            if linea_recibida.startswith("COMMS"):
                messagebox.showwarning("Tierra", "Error en las comunicaciones")
                registrar_evento("ALARMA", "Error de comunicaciones")
            if linea_recibida.startswith("Barrido"):
                registrar_evento("COMANDO", "Servo en barrido")
                messagebox.showinfo("Información","Giro del servo automático (Barrido)")
            if linea_recibida.startswith("Manual"):
                registrar_evento("COMANDO", "Servo en manual")
                messagebox.showinfo("Información", "Giro del servo manual. Usa el joystick para que gire el servo.")

    except Empty:
        pass
    if updated_orbit:
        actualizar_ground_track(x_vals, y_vals, z_vals)

        tnow = time.time()
        if tnow - ultimo_update_orbita >= 1.0 / FPS_ORBITA:
            actualizar_orbita()
            ultimo_update_orbita = tnow

    actualizar_grafica_gui()
    actualitzar_grafica_humedad()
    actualizar_grafica_medias()

    if mostrar_radar:
        canvas_radar.draw_idle()

    root.after(100, process_serial_queue)

#Actualización de la gráfica de temperatura
def actualizar_grafica_gui():
    ax_temp.clear()
    ax_temp.set_xlim(0, max(20, len(eje_x)))
    ax_temp.set_ylim(0, 50)
    ax_temp.plot(eje_x, temperaturas, marker='o', linestyle='-', color='red')
    ax_temp.set_title('Temperatura en tiempo real')
    ax_temp.set_xlabel('Muestras')
    ax_temp.set_ylabel('Temperatura (°C)')
    try:
        canvas_temp.draw()
    except Exception as e:
        print("Error al dibujar temperatura:", e)
#Actualización de la gráfica de las medias
def actualizar_grafica_medias():
    ax_medias.clear() # angulo
    ax_medias.set_xlim(0, max(20, i))
    ax_medias.set_ylim(0, 50)

    # Solo dibujar si hay valores
    valores = [m for m in mitjana_temperatures if m is not None]
    if valores:
        ax_medias.plot(eje_x_medias, valores, marker='o', linestyle='-', color='orange')

    ax_medias.set_title('Medias de temperatura en tiempo real')
    ax_medias.set_xlabel('Muestras')
    ax_medias.set_ylabel('Temperatura media (°C)')
    canvas_medias.draw()
#Actualización de la gráfica de humedad
def actualitzar_grafica_humedad():
    ax_hum.clear()
    ax_hum.set_xlim(0,max(20, len(eje_x)))
    ax_hum.set_ylim(0, 100)
    ax_hum.plot(eje_x, humedades, marker='o', linestyle='-', color='blue')
    ax_hum.set_title('Humedad en tiempo real')
    ax_hum.set_xlabel('Muestras')
    ax_hum.set_ylabel('Humedad (%)')
    try:
        canvas_hum.draw()
    except Exception as e:
        print("Error al dibujar humedad:", e)



#Definimos las diferentes funciones de los botones: Iniciar, Parar y Reanudar
def iniciar():
    global running, hilo_serial
    if not running:
        running = True
        mySerial.write(b'Iniciar\n')
        registrar_evento("COMANDO", "Iniciar lectura de datos")
        if hilo_serial is None or not hilo_serial.is_alive():
            hilo_serial = threading.Thread(target=recepcion, daemon=True)
            hilo_serial.start()
        root.after(100, process_serial_queue)

def parar():
    global running
    running = False
    mySerial.write(b'Parar\n')
    registrar_evento("COMANDO", "Parar lectura de datos")
    messagebox.showinfo("Info", "Lectura detenida")

def reanudar(): # 
    global running, hilo_serial
    if not running:
        running = True
        mySerial.write(b'Reanudar\n')
        registrar_evento("COMANDO", "Reanudar lectura de datos")
        if hilo_serial is None or not hilo_serial.is_alive():
            hilo_serial = threading.Thread(target=recepcion, daemon=True)
            hilo_serial.start()
        messagebox.showinfo("Info", "Lectura reanudada")

#Definimos los botones para el cambio de gráfico
def mostrar_grafico_temp():
    global mostrar_radar, mostrar_medias, mostrar_temperaturas
    mostrar_temperaturas = True
    mostrar_radar = False
    mostrar_medias = False
    grafica_frame.tkraise()

def mostrar_grafico_radar():
    global mostrar_radar, mostrar_medias, mostrar_temperaturas
    mostrar_temperaturas = False
    mostrar_radar = True
    mostrar_medias = False
    radar_frame.tkraise()
    try:
        canvas_radar.draw()
    except Exception as e:
        print("Error dibujando radar al mostrar:", e)

def mostrar_grafico_medias():
    global mostrar_radar, mostrar_medias
    mostrar_radar = False
    mostrar_medias = True
    medias_frame.tkraise()
    actualizar_grafica_medias()

def mostrar_orbita_3d():
    orbita_3d_frame.tkraise()

def mostrar_groundstation():
    mapa_frame.tkraise()

def mostrar_grafico_humedad():
    humedad_frame.tkraise()

#Función para que el usuario pueda cambiar el periodo de transmisión
def cambiar_periodo():
    nuevo = simpledialog.askinteger(
        "Periodo de transimisón",
        "Introduce el nuevo periodo de transimisión en milisegundos:",
        minvalue = 100
    )
    if nuevo is not None:
        comando = "PERIODO:{}\n".format(nuevo)
        mySerial.write(comando.encode())
        messagebox.showinfo("Periodo actualizado", f"Nuevo periodo: {nuevo} ms")

#Función para que las medias se hagan en el satélite
def medias_satelite():
    global medias_python, medias_ard
    medias_ard = True
    medias_python = False
    mySerial.write(b'Medias\n')
    messagebox.showinfo("Medias", "Petición de medias enviada al satélite. La respuesta aparecerá cuando llegue.")

#Función para que las medias se caluclen en tierra.
def medias_tierra():
    global medias_python, medias_ard
    medias_python = True
    medias_ard = False
    mySerial.write(b'MediaStop\n')
    messagebox.showinfo("Media Tierra", "Petición MediaStop enviada. Calcula la media localmente desde la lista 'temperaturas'.")

#Función que sirve para establecer el límite de temperatura indicado por el usuario.
def limite_usu():
    global limite, alarma_limite
    try:
        nuevo = simpledialog.askinteger(
            "Limite de medias",
            "Introduce el nuevo limite de temperaturas:",
            minvalue = 0,
            maxvalue = 30
        )
        if nuevo is not None:
            limite = nuevo
            messagebox.showinfo(f"Nuevo limite: {limite} ºC")
            alarma_limite = True
    except Exception as e2:
        print("Error (limite):", e2)

#Función para registrar cuando el usuario  haga una observación y luego aparezca en la tabla de eventos.
def registrar_observacion():
    descripcion = simpledialog.askstring("Observación", "Introduce tu observación:")

    if descripcion is None or descripcion.strip() == "":
        messagebox.showwarning("Aviso", "No se escribió ninguna observación.")
        return

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{fecha} | USUARIO | {descripcion.strip()}\n"

    try:
        with open("eventos.txt", "a", encoding="utf-8") as f:
            f.write(linea)
        messagebox.showinfo("Guardado", "Observación registrada correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar la observación:\n{e}")



#CÓDIGO INTERFAZ GRÁFICA
root = tk.Tk()                              
root.geometry("1200x950")                   
root.title("Interfaz gráfica")  

#Configuración de las columnas y filas para que tengan el mismo tamaño
root.grid_rowconfigure(0, weight=1)   
root.grid_rowconfigure(1, weight=1)   
root.grid_rowconfigure(2, weight=1)   
root.grid_rowconfigure(3, weight=1)  
root.grid_rowconfigure(4, weight=1)   
root.grid_rowconfigure(6, weight=1)

root.grid_columnconfigure(0, weight=3)   
root.grid_columnconfigure(1, weight=10)   
root.grid_columnconfigure(2, weight=1)   

arduino_conectado = False

try:
    mySerial = serial.Serial(device, 9600, timeout=1)
    arduino_conectado = True
    print("Arduino conectado correctamente en", device)
except serial.SerialException as e:
    print("No se pudo abrir el puerto:", e)
    #mySerial = None   # MUY IMPORTANTE
    arduino_conectado = False 

for r in (0, 1, 2):
    root.grid_rowconfigure(r, weight=1, uniform="control")

# Frame único de botones
frame_botones = tk.LabelFrame(root, text="Control")
frame_botones.grid(row=0, column=0, rowspan=3, padx=5, pady=4, sticky="nsew")

for i in range(3):
    frame_botones.rowconfigure(i, weight=1)

frame_botones.columnconfigure(0, weight=1) 
#Definimos el botón iniciar
button_iniciar_frame = tk.LabelFrame(frame_botones, text="Iniciar")
button_iniciar_frame.grid(row=0, column=0, padx=5, pady=4, sticky="nsew")
button_iniciar_frame.rowconfigure(0, weight=1)
button_iniciar_frame.columnconfigure(0, weight=1)
tk.Button(button_iniciar_frame, text="Iniciar", bg="red", fg="white", command=iniciar).grid(sticky="nsew", padx=7, pady=5)

#Definimos el botón parar
button_parar_frame = tk.LabelFrame(frame_botones, text="Parar")
button_parar_frame.grid(row=1, column=0, padx=5, pady=4, sticky="nsew")
button_parar_frame.rowconfigure(0, weight=1)
button_parar_frame.columnconfigure(0, weight=1)
tk.Button(button_parar_frame, text="Parar", bg="blue", fg="white",command=parar).grid(sticky="nsew", padx=7, pady=5)

#Definimos el botón reanudar
button_reanudar_frame = tk.LabelFrame(frame_botones, text="Reanudar")
button_reanudar_frame.grid(row=2, column=0, padx=5, pady=4, rowspan =1, sticky="nsew")
button_reanudar_frame.rowconfigure(0, weight=1)
button_reanudar_frame.columnconfigure(0, weight=1)
tk.Button(button_reanudar_frame, text="Reanudar", bg="white", fg="black",command=reanudar).grid(sticky="nsew", padx=7, pady=5)

#Definimos el botón de cambiar de periodo
button_periodo_frame = tk.LabelFrame(root, text="Cambiar periodo")
button_periodo_frame.grid(row=3, column=0, padx=5, pady=4, sticky="nsew")
button_periodo_frame.rowconfigure(0, weight=1)
button_periodo_frame.columnconfigure(0, weight=1)
tk.Button(button_periodo_frame, text="Cambiar periodo", bg="orange", fg="black", command=cambiar_periodo).grid(sticky="nsew", padx=7, pady=5)


#Definimos los botones para cambiar de gráfica
button_selector_frame = tk.LabelFrame(root, text="Seleccionar gráfico")
button_selector_frame.grid(row=6, column=0, padx=5, pady=5, sticky="new",columnspan=2)
button_selector_frame.rowconfigure(0, weight=1)
button_selector_frame.columnconfigure(0, weight=1)
tk.Button(button_selector_frame, text="Ver gráfica temperatura", bg="lightgreen", command=mostrar_grafico_temp).grid(sticky="ew", padx=5, pady=4, rowspan =1, columnspan=2)
tk.Button(button_selector_frame, text="Ver Radar", bg="lightblue", command=mostrar_grafico_radar).grid(sticky="ew", padx=5, pady=4, rowspan =1, columnspan =2)
tk.Button(button_selector_frame, text="Ver medias temperatura", bg="cyan", command=mostrar_grafico_medias).grid(sticky="ew", padx=5, pady=4, rowspan =1, columnspan = 2)
tk.Button(button_selector_frame, text="Ver gráfico humedad", bg="orange", command=mostrar_grafico_humedad).grid(sticky="ew", padx=5, pady=4, rowspan =1, columnspan = 2)

#Definimos el botón decidir donde calcular las medias y el límite de medias
button_selector2_frame = tk.LabelFrame(root, text="Cálculo de medias")
button_selector2_frame.grid(row=4, column=0, padx=3, pady=3, sticky="new")
button_selector2_frame.rowconfigure(0, weight=0)
button_selector2_frame.columnconfigure(0, weight=1)
tk.Button(button_selector2_frame, text="En satélite", bg="violet", command=medias_satelite).grid(row=0, column=0, sticky="ew", padx=5, pady=4)
tk.Button(button_selector2_frame, text="En tierra", bg="green",command=medias_tierra).grid(row=1, column=0, sticky="ew", padx=5, pady=4)
tk.Button(button_selector2_frame, text="Límite medias", bg="white", fg="black", command=limite_usu).grid(row=2, column=0, sticky="ew", padx=5, pady=4)

#CÓDIGO DE LAS TEMPERATURAS
#Frame de la gráfica de temperatura
grafica_frame = tk.LabelFrame(root, text="Gráfica de temperatura")
grafica_frame.grid(row=0, column=1, rowspan=5, padx=5, pady=5, sticky="nsew")
grafica_frame.columnconfigure(0, weight=1)
grafica_frame.rowconfigure(0, weight=1)

#Creamos los canvas para que aparezca la gráfica
fig_temp, ax_temp = plt.subplots(figsize=(6, 4))
canvas_temp = FigureCanvasTkAgg(fig_temp, master=grafica_frame)
canvas_temp.draw()
canvas_temp.get_tk_widget().grid(row=0, column=0, sticky="nsew")


#Creamos los canvas para que aparezca la gráfica de temperatura
fig_temp, ax_temp = plt.subplots(figsize=(6, 4))
canvas_temp = FigureCanvasTkAgg(fig_temp, master=grafica_frame)
canvas_temp.draw()
canvas_temp.get_tk_widget().grid(row=0, column=0, sticky="nsew")

#CÓDIGO GRÁFICA HUMEDAD
humedad_frame = tk.LabelFrame(root, text = "Gráfica de humedad")
humedad_frame.grid(row =0, column=1, rowspan=5, padx=5, pady=5, sticky="nsew")
humedad_frame.columnconfigure(0, weight=1)
humedad_frame.rowconfigure(0, weight=1)
#Creamos los canvas para que aparezca la gráfica
fig_hum, ax_hum = plt.subplots(figsize=(6,4))
canvas_hum = FigureCanvasTkAgg(fig_hum, master=humedad_frame)
canvas_hum.draw()
canvas_hum.get_tk_widget().grid(row=0, column=0, sticky="nsew")

#CÓDIGO DE LAS MEDIAS
#Frame de la gráfica de las medias de temperatura
medias_frame = tk.LabelFrame(root, text="Gráfica de medias temperatura")
medias_frame.grid(row=0, column=1, rowspan=5, padx=5, pady=5, sticky="nsew")
medias_frame.columnconfigure(0, weight=1)
medias_frame.rowconfigure(0, weight=1)

#Creamos los canvas para que aparezca la gráfica de temperatura
fig_medias, ax_medias = plt.subplots(figsize=(6,4))
canvas_medias = FigureCanvasTkAgg(fig_medias, master=medias_frame)
canvas_medias.draw()
canvas_medias.get_tk_widget().grid(row=0, column=0, sticky="nsew")
canvas_medias.get_tk_widget().config(width=600, height=400)  

#CÓDIGO DEL RADAR
#Frame del radar
radar_frame = tk.LabelFrame(root, text="Radar Ultrasónico")
radar_frame.grid(row=0, column=1, rowspan=5, padx=5, pady=5, sticky="nsew")
radar_frame.columnconfigure(0, weight=1)
radar_frame.rowconfigure(0, weight=1)

fig_radar = plt.Figure(figsize=(6, 4)) # FALLO
ax_radar = fig_radar.add_subplot(111, polar=True)
ax_radar.set_title("Radar Ultrasónico", va='bottom')
ax_radar.set_rlim(0, 100)
ax_radar.set_thetamin(0)
ax_radar.set_thetamax(180)
ax_radar.set_theta_zero_location('E')
ax_radar.set_theta_direction(1)
ax_radar.set_rlabel_position(0)

linea, = ax_radar.plot([], [], linewidth=2, color='green')
punto, = ax_radar.plot([], [], 'o', markersize=8, color='green')
texto = ax_radar.text(np.deg2rad(90), 52, "", ha='center', va='center', fontsize=10, color='black')

#Creamos los canvas para que aparezca el radar
canvas_radar = FigureCanvasTkAgg(fig_radar, master=radar_frame)
canvas_radar.draw()
canvas_radar.get_tk_widget().grid(row=0, column=0, sticky="nsew")


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

#ÓRBITA

R_EARTH = 6371000

# Frame orbita
orbita_frame = tk.LabelFrame(root, text="Órbita del satélite")
orbita_frame.grid(row=3, column=2, rowspan=5, padx=5, pady=5, sticky="nsew")
orbita_frame.columnconfigure(0, weight=1)
orbita_frame.rowconfigure(0, weight=1)
#Para que haya dos frames: uno con la órbita 3d y el otro con el mapa
orbita_3d_frame = tk.Frame(orbita_frame)
mapa_frame = tk.Frame(orbita_frame)
mapa_frame.rowconfigure(0, weight=1)
mapa_frame.columnconfigure(0, weight=1)
orbita_3d_frame.rowconfigure(0, weight=1)
orbita_3d_frame.columnconfigure(0, weight=1)

for f in (orbita_3d_frame, mapa_frame):
    f.grid(row=0, column=0, sticky="nsew")

escoger_orbita_frame = tk.LabelFrame(root, text = "Tipo de órbita")
escoger_orbita_frame.grid(row =7, column = 0, padx = 5, pady =5, sticky = "nsew", columnspan=2)
escoger_orbita_frame.columnconfigure(0, weight=1)
escoger_orbita_frame.rowconfigure(0, weight=1)
escoger_orbita_frame.rowconfigure(1, weight=1)
tk.Button(escoger_orbita_frame, text="Órbita 3D", bg= "green" ,command=mostrar_orbita_3d).grid(row=0, column=0, sticky="ew", padx=5, pady=4)
tk.Button(escoger_orbita_frame, text = "Groundstation", bg = "grey", command=mostrar_groundstation).grid(row=1, column=0, sticky ="ew", padx =5, pady =4)

#CÓDIGO ORBITA 3D
#Figura 3D
fig_orbita = plt.figure(figsize=(6, 4))
ax_orbita = fig_orbita.add_subplot(111, projection='3d')

canvas_orbita = FigureCanvasTkAgg(fig_orbita, master=orbita_3d_frame)
canvas_orbita.get_tk_widget().grid(row=0, column=0, sticky="nsew")

ax_orbita.view_init(elev=25, azim=45)      
ax_orbita.set_box_aspect([1, 1, 1])         

lim = R_EARTH * 1.15
ax_orbita.set_xlim(-lim, lim)
ax_orbita.set_ylim(-lim, lim)
ax_orbita.set_zlim(-lim, lim)

ax_orbita.set_xlabel("X (m)")
ax_orbita.set_ylabel("Y (m)")
ax_orbita.set_zlabel("Z (m)")
ax_orbita.grid(True)

u = np.linspace(0, 2 * np.pi, 40)
v = np.linspace(0, np.pi, 40)

x_earth = R_EARTH * np.outer(np.cos(u), np.sin(v))
y_earth = R_EARTH * np.outer(np.sin(u), np.sin(v))
z_earth = R_EARTH * np.outer(np.ones_like(u), np.cos(v))

ax_orbita.plot_wireframe(
    x_earth, y_earth, z_earth,
    color='orange',
    linewidth=0.5,
    alpha=0.6
)

orbita_plot, = ax_orbita.plot(
    [], [], [],
    color='blue',
    linewidth=2,
    label='Órbita satélite'
)


ultimo_point_plot = ax_orbita.scatter(
    [], [], [],
    color='red',
    s=50,
    label='Último punto'
)

ax_orbita.legend(loc='upper right')

canvas_orbita.draw()
# Función de actualización
def actualizar_orbita():
    if not x_vals:
        return

    # Actualizar trayectoria completa
    orbita_plot.set_data(x_vals, y_vals)
    orbita_plot.set_3d_properties(z_vals)

    # Actualizar último punto
    ultimo_point_plot._offsets3d = ([x_vals[-1]], [y_vals[-1]], [z_vals[-1]])

    # Auto-ajustar límites para que todo quede centrado
    max_range = max(
        max(map(abs, x_vals)),
        max(map(abs, y_vals)),
        max(map(abs, z_vals)),
        R_EARTH
    ) * 1.3

    ax_orbita.set_xlim(-max_range, max_range)
    ax_orbita.set_ylim(-max_range, max_range)
    ax_orbita.set_zlim(-max_range, max_range)

    ax_orbita.set_box_aspect([1, 1, 1])  # proporción 1:1:1
    ax_orbita.set_title("Órbita del satélite en 3D")

    canvas_orbita.draw()

#CÓDIGO GROUNDSTATION
# Figura 2D
fig_mapa = plt.figure(figsize=(8, 4))
ax_mapa = fig_mapa.add_subplot(111)

canvas_mapa = FigureCanvasTkAgg(fig_mapa, master=mapa_frame)
canvas_mapa.get_tk_widget().grid(row=0, column=0, sticky="nsew")

ax_mapa.set_xlim(-180, 180)
ax_mapa.set_ylim(-90, 90)

ax_mapa.set_xlabel("Longitud [°]")
ax_mapa.set_ylabel("Latitud [°]")
ax_mapa.set_title("Ground Track del Satélite")

ax_mapa.grid(True)

# Líneas de referencia
ax_mapa.axhline(0, color='green', linewidth=1, label="Ecuador")
ax_mapa.axvline(0, color='orange', linewidth=1, label="Meridiano 0°")

from matplotlib import image as mpimg
import os

map_img_path = os.path.join(os.path.dirname(__file__), "mapa_groundstationt.png")

try:
    world_img = mpimg.imread(map_img_path)

    ax_mapa.imshow(
        world_img,
        extent=[-180, 180, -90, 90],  # lon_min, lon_max, lat_min, lat_max
        origin='upper',
        zorder=0
    )
except FileNotFoundError:
    print("No s'ha trobat la imatge del mapa")
ground_track_plot, = ax_mapa.plot(
    [], [],
    color='cyan',
    linewidth=2,
    zorder=3,
    label="Órbita proyectada"
)
# Último punto
ground_ultimo_point = ax_mapa.scatter(
    [], [],
    color='red',
    s=50,
    zorder=5,
    label="Última posición"
)
ax_mapa.legend(loc="upper right")
canvas_mapa.draw()

def xyz_to_latlon(x, y, z):
    r = np.sqrt(x**2 + y**2 + z**2)
    lat = np.degrees(np.arcsin(z / r))
    lon = np.degrees(np.arctan2(y, x))
    lon = (lon + 180) % 360 - 180  # normalizar
    return lat, lon

#Actualizar
def actualizar_ground_track(x_vals, y_vals, z_vals):
    if len(x_vals) < 1:
        return
    lat, lon = xyz_to_latlon(np.array(x_vals), np.array(y_vals), np.array(z_vals))
    ground_track_plot.set_data(lon, lat)
    ground_ultimo_point.set_offsets([[lon[-1], lat[-1]]])
    canvas_mapa.draw()



#CÓDIGO REGISTRO DE EVENTOS

#Función para registrar observación
def registrar_observacion():
    descripcion = entrada_observaciones.get()
    if descripcion.strip() == "":
        messagebox.showwarning("Aviso", "Debes introducir una observación")
        return
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{fecha} | OBSERVACION | {descripcion}\n"
    with open("eventos.txt", "a", encoding="utf-8") as f:
        f.write(linea)
    messagebox.showinfo("Guardado", "Observación registrada")
    entrada_observaciones.delete(0, tk.END)
    cargar_eventos()  

#Función para registrar un evento
def registrar_evento(tipo, descripcion):
    if "FALLO" in descripcion.upper():  
        tipo = "ALARMA"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"{fecha} | {tipo} | {descripcion}\n"
    with open("eventos.txt", "a", encoding="utf-8") as f:
        f.write(linea)
    print(f"Evento registrado: {linea.strip()}")  

#Función para filtrar  eventos
def filtrar_eventos():
    tipo = var_tipo.get()
    fecha_txt = entrada_date.get().strip()
    fecha_filtro = None
    if fecha_txt:
        try:
            fecha_filtro = datetime.strptime(fecha_txt, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror(
                "Error",
                "La fecha debe tener el formato YYYY-MM-DD\nEjemplo: 2025-01-01"
            )
            return
    #Se limpia la tabla
    tabla.delete(*tabla.get_children())

    try:
        with open("eventos.txt", "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        messagebox.showerror("Error", "No existe el fichero eventos.txt")
        return

    #Se aplican los filtros
    for linea in lineas:
        partes = linea.strip().split(" | ")
        if len(partes) != 3:
            continue
        fecha_evento_txt, tipo_evento, descripcion = partes
        try:
            fecha_evento = datetime.strptime(
                fecha_evento_txt, "%Y-%m-%d %H:%M:%S"
            ).date()
        except ValueError:
            continue
        #El filtro por tipo de evento
        if tipo != "TODOS" and tipo_evento != tipo:
            continue
        #El filtro por fecha
        if fecha_filtro and fecha_evento != fecha_filtro:
            continue
        tabla.insert("", "end", values=(fecha_evento_txt, tipo_evento, descripcion))


#FRAME CONTROL DE LOS EVENTOS
control_eventos_frame = tk.LabelFrame(root, text = "Eventos")
control_eventos_frame.grid(row=0, column = 2, padx = 5, pady =5, sticky="nnew", rowspan = 2)
control_eventos_frame.rowconfigure(0, weight=1)
control_eventos_frame.columnconfigure(0, weight=1)


registro_frame = tk.LabelFrame(control_eventos_frame, text="Registro de eventos")
registro_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew", columnspan = 1)
registro_frame.rowconfigure(0, weight=1)
registro_frame.columnconfigure(0, weight=1)

tk.Label(registro_frame, text="Observación del usuario:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
entrada_observaciones = tk.Entry(registro_frame, width=70)
entrada_observaciones.grid(row=1, column=0, padx=5, pady=5, sticky="nsew", columnspan=2)

button_guardar = tk.Button(registro_frame, text="Guardar observación", bg = "cyan",command=registrar_observacion)
button_guardar.grid(row=2, column=0, padx=5, pady=5, sticky="nsw")

#FRAME PARA FILTRAR EVENTOS
filtrar_frame = tk.LabelFrame(control_eventos_frame, text="Filtrar eventos")
filtrar_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

# Tipo de evento
tk.Label(filtrar_frame, text="Tipo de evento:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
var_tipo = tk.StringVar()

tipo = ttk.Combobox(filtrar_frame, textvariable=var_tipo, values =["TODOS", "COMANDO", "ALARMA", "OBSERVACION"] )
tipo.current(0) #Esto sirve para que por defecto nos salga [TODOS] al principio
tipo.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

# Fecha
tk.Label(filtrar_frame, text="Filtrar por fecha (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
entrada_date = ttk.Entry(filtrar_frame, width=30)
entrada_date.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

# Botón aplicar filtro
button_filtrar = tk.Button(filtrar_frame, text="Aplicar filtros", bg="yellow", command=filtrar_eventos)
button_filtrar.grid(row=2, column=1, padx=5, pady=5, sticky="ensw")

#FRAME RESULTADOS
resultados_frame = tk.LabelFrame(control_eventos_frame, text="Resultados búsqueda")
resultados_frame.grid(row=2, column=0, padx=8, pady=5, sticky="nsew")
resultados_frame.rowconfigure(0, weight=1)
resultados_frame.columnconfigure(0, weight=1)
tabla_resultados = ttk.Frame(resultados_frame, width=50, height=10)
tabla_resultados.grid(row=0, column = 0,  padx = 0, pady=0, sticky="nsew")
tabla_resultados.rowconfigure(0, weight=1)
tabla_resultados.columnconfigure(0, weight=1)
columnas_tabla= ("Fecha", "Tipo", "Descripción")
tabla = ttk.Treeview(tabla_resultados, columns=columnas_tabla, show="headings") #Utilizamos el Treeview para que se vean las columnas
tabla.grid(row=0, column=0, sticky="nsew")

#Configuración de la tabla
for col in columnas_tabla:
    tabla.heading(col, text=col)
    tabla.column(col, width=120)
scroll = ttk.Scrollbar(tabla_resultados, orient="vertical", command=tabla.yview)
scroll.grid(row=0, column=1, sticky="ns")
tabla.configure(yscrollcommand=scroll.set)

#Función para cargar todos los eventos al inicio
def cargar_eventos():
    try:
        with open("eventos.txt", "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        return
    tabla.delete(*tabla.get_children()) #Al ser Treeview tienes que ponerlo así

    for linea in lineas:
        partes = linea.strip().split(" | ")
        if len(partes) == 3:
            tabla.insert("", "end", values=partes)
cargar_eventos()  # Cargar al iniciar


#Ejecutar interfaz:
root.mainloop()