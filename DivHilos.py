import socket
import threading
#CONEXION INICIAL DE RECONOCIMIENTO CON EL SERVIDOR INTERMEDIO
ms=("medio.calcseeking.com",5500)
sSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creamos un socket Tcp/Ip
sSocket.connect(ms)
Id=sSocket.recv(1024)
sSocket.send("-")
MiIp=sSocket.recv(1024)
sSocket.send("7000")
sSocket.close



#socket conexion para el servicio de dividir
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creamos un socket Tcp/Ip
serverSocket.bind((MiIp, 7000)) # Establecemos la Ip y el Puerto de comunicacion
serverSocket.listen(10) # Establecemos la cantidad de clientes que espera el servidor


def clientCustomer(*args):
	socketConnection = args[0]
	clientAddress = args[1]
	while True: # se esperan nuevos mensajes
		received = socketConnection.recv(1024) # capturamos el mensaje de maximo 1024 bytes
		if received: # mientras existan mensajes
			if received == "": # si es un mensaje de salida
				print "conexion con ", clientAddress, "terminada"
				socketConnection.close() # cerramos la conexion
				break

			else:
				print "Recibido: ", received # mostramos el mensaje recibido
				stringReceived = received.split(",")
				numberA = float(stringReceived[1])
				numberB = float(stringReceived[2])
				socketConnection.send(str(numberA / numberB))
				print "Listo <3 :* carlis"
				#socketConnection.close()

while True: # esperamos conexiones

	print "Servidor de Division"
	print "Esperando conexion"
	socketConnection, clientAddress = serverSocket.accept() # si hay conexion
	print "Conexion desde: ", clientAddress # mostramos la Ip del cliente
	threading.Thread(target = clientCustomer, args = (socketConnection, clientAddress)).start() # creamos un hilo para nuevas conexiones
