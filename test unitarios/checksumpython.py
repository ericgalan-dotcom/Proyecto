t = 23.40
h = 52.00
dist = 30.40
ang = 15.00
checksum = 246

trozos = ["T",f"{t:.2f}","H",f"{h:.2f}","D",f"{dist:.2f}","A",f"{ang:.2f}",checksum]

checksum_recibido = int(trozos[-1])
datos = trozos[:-1]
mens = "".join(datos)
checksum_calculado = 0
print(datos)
checksum_calculado = sum(ord(c) for c in mens) % 256

print(checksum_calculado)    
print(checksum_recibido)               
if checksum_calculado != checksum_recibido:
    print("Checksum incorrecto, mensaje descartado")

if checksum_calculado == checksum_recibido:
    print("Mensaje válido")