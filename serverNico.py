#!/usr/bin/env python3

import pika
import uuid
import random
import threading
import os
import sys
import time
import operator
import tkinter as tkinter
import pygame

#IP="localhost"
IP="www.nidal.online"

class rabbitmqClient:
	def __init__(self, ip=IP):
		#rabbitmq
		self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=ip, socket_timeout=2))
		self.channel = self.connection.channel()
		self.channel.queue_declare(queue="conectoSitio")
		self.channel.queue_declare(queue="conectoMesa")
		self.channel.queue_declare(queue="atencionMesas")
		self.channel.basic_consume(self.receiveSitio, queue="conectoSitio")
		self.channel.basic_consume(self.receiveAtencionMesas, queue="atencionMesas", no_ack=True)
		self.channel.basic_consume(self.receiveMesa, queue="conectoMesa", no_ack=True)
		self.channel.basic_qos(prefetch_count=1)
		
		self.SitiosCodigo={}#codigo sitio, con la respectiva cola donde enviar respuestas
		self.cancionesSitio={}#codigo sitio , con su liestado de cacniones 
		self.votosCanciones={}#guarda id dee canciones coen sus respectivos votos
		self.mesasSitios={}#guarda para cada sitio el listado de las mesas actuales ej mesasSitio[sjfh34m]=(jff,jdkf,kej) 
		self.listSitios=[]
		self.listMesas=[]
		self.listClientesWeb=["un cliente web"]
		self.listClientesAPP=["un cliente APP"]

		
		#Tkinter
		self.root = tkinter.Tk()
		self.root.wm_title("Servicio de Reproducción")
		scrollbar = tkinter.Scrollbar(self.root, orient=tkinter.VERTICAL)
		self.textoBox = tkinter.Text(self.root, height=8, width=45, yscrollcommand=scrollbar.set)# controla el tamaño del Textobox
		self.textoBox2 = tkinter.Text(self.root, height=8, width=45, yscrollcommand=scrollbar.set)# controla el tamaño del Textobox2
		scrollbar.config(command=self.yview)
		scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
		
		self.textoBox.pack(side=tkinter.LEFT, fill=tkinter.Y)
		self.textoBox.config(state=tkinter.DISABLED)
		self.textoBox2.pack(side=tkinter.LEFT, fill=tkinter.Y)
		self.textoBox2.config(state=tkinter.DISABLED)
		frame = tkinter.Frame(self.root)
		frame.pack()

		#list
		self.list = tkinter.Listbox(self.root, selectmode=tkinter.SINGLE, yscrollcommand=scrollbar.set, exportselection=False)
		self.list2 = tkinter.Listbox(self.root, selectmode=tkinter.SINGLE, yscrollcommand=scrollbar.set, exportselection=False)
		self.list3 = tkinter.Listbox(self.root, selectmode=tkinter.SINGLE, yscrollcommand=scrollbar.set, exportselection=False)
		#self.list.bind('<<ListboxSelect>>', self.showInfoSong)
		self.list.pack(fill=tkinter.BOTH, expand=1)
		self.list2.pack(fill=tkinter.BOTH, expand=1)
		self.list3.pack(fill=tkinter.BOTH, expand=1)

		# self.command = tkinter.StringVar()
		# tkinter.Entry(frame, textvariable=self.command).grid(row=1, column=1)
		tkinter.Label(frame, text='State:').grid(row=0, column=0)
		self.answer = tkinter.StringVar()
		self.answer.set("Stoped")
		tkinter.Label(frame, textvariable=self.answer).grid(row=0, column=1)

		

		self.buttonUpdate = tkinter.Button(frame, text='Update List', command=self.updateListBox)
		self.buttonUpdate.grid(row=1, column=0, columnspan=1)

		# self.buttonUpdate.config(state=tkinter.DISABLED)

		
		

	def yview(self, *args):
		self.textoBox.yview(*args)
		self.textoBox2.yview(*args)
		self.list.yview(*args)

	def printBox1(self, value):# Maneja el log
		self.textoBox.config(state=tkinter.NORMAL)
		self.textoBox.insert(tkinter.END, "\n"+time.asctime(time.localtime(time.time()))+": "+str(value))
		self.textoBox.see(tkinter.END)
		self.textoBox.config(state=tkinter.DISABLED)

	def printBox2(self, value):
		self.textoBox2.config(state=tkinter.NORMAL)
		self.textoBox2.delete('1.0', tkinter.END)
		self.textoBox2.insert(tkinter.END, str(value))
		self.textoBox2.see(tkinter.END)
		self.textoBox2.config(state=tkinter.DISABLED)

	def deletePrintBox2(self, value):
		self.textoBox2.config(state=tkinter.NORMAL)
		self.textoBox2.delete('1.0', tkinter.END)
		self.textoBox2.see(tkinter.END)
		self.textoBox2.config(state=tkinter.DISABLED)
		
	def updateListBox(self):
		self.list.delete(0, tkinter.END)#Borra TODO
		for lugar in self.listSitios:
			self.list.insert(tkinter.END, lugar)
		self.list2.delete(0, tkinter.END)#Borra TODO
		for lugar in self.mesasSitios:
			self.list2.insert(tkinter.END, lugar+":"+str(self.mesasSitios[lugar]))
		self.list3.delete(0, tkinter.END)#Borra TODO
		for lugar in self.listClientesAPP:
			self.list3.insert(tkinter.END, lugar)


	

	def createTempQueue(self,body):
		#queueName = result.method.queue
		codigo=self.GenerarCodigo()
		self.channel.queue_declare(queue=codigo,exclusive=True)#temporal queue
		#mensajeInicial=queueName+','+ codigo
		#print(mensajeInicial)
		self.SitiosCodigo[codigo]=body
		self.mesasSitios[codigo]=[]
		print("SITIOS:",self.SitiosCodigo)
		self.channel.basic_qos(prefetch_count=1)#set number of messages resolve or consume (this case 1 at time)
		self.channel.basic_consume(self.receivecolaSitio, queue=codigo, no_ack=True)
		self.channel.basic_publish(exchange='', routing_key=body, body=codigo,properties=pika.BasicProperties(delivery_mode=2,))
		
		#return queueName

	
	#def receiveSitioAlone(self, ch, method, properties, body):


	def receiveSitio(self, ch, method, properties, body):
		body=body.decode("utf-8")
		self.printBox1("Mensaje recibido de un sitio {}".format(body))
		if(not body in self.listSitios and "amq" in body):
		
			self.listSitios.append(body)
			tempQueueName=threading.Thread(target=self.createTempQueue(body))
			#print("cola",tempQueueName)
			#self.channel.basic_consume(self.receiveSitioAlone, queue=tempQueueName, no_ack=True)
			#self.channel.basic_publish(exchange='', routing_key=body, body=tempQueueName)
			#print(body)
		ch.basic_ack(delivery_tag=method.delivery_tag)	
	def ConvertLista(self,lista):
		aux=""
		for enum, valor in enumerate(lista):
			if(enum==0):
				aux=str(valor)
			else:
				aux=aux+"|||"+str(valor)
		return aux.replace("'", '"').replace('"["', '"').replace('"]"', '"')


	def updatePeriodica(self):
		#print(self.cancionesSitio)
		for dic in self.cancionesSitio:
			canciones={}
			votos={}
			canciones=self.cancionesSitio[dic].copy()							
			#print(canciones)
			#print(self.listadicc(canciones),"JAJAJA",self.cancionesSitio[dic])
			votos=self.votosCanciones[dic].copy()
			songActual=canciones.pop(0)
			del votos[list(songActual.keys())[0]] #elimina la cancion actaul de la lista de votos
			newCanciones,CAMBIO=self.ordenar(canciones,votos)
			#print("return",self.listadicc(newCanciones))
			newCanciones.insert(0,songActual)
			#print(songActual)
			mensaje=self.listadicc(newCanciones)
			mensaje=self.listadicc(newCanciones)
			print("Actualizo")
			#print("FINNNN")
			#print (CAMBIO,mensaje)
			
			self.multidifucion(self.channel,self.mesasSitios[dic],self.ConvertLista(newCanciones))  #difucion a todos, con lista de mesas del sitio y canciones actulizadas



		#self.printBox2("resultado {}".format(body.decode("utf-8")))'''
		self.buttonUpdate.after(5000, self.updatePeriodica)
	def receivecolaSitio(self, ch, method, properties, body):
		
		body=body.decode("utf-8")
		#print (body)
		temporal=body.split("`")
		#self.printBox1("Canciones {}".format(temporal[1]))
		if temporal[0]=="listaInicial":
			aux=eval(temporal[1])
			
			self.cancionesSitio[method.routing_key]=aux
			self.votosCanciones[method.routing_key]={}
			#crear diccionario con la lista de canciones , inicializada en 0
			for lista in aux:
				#print (list(lista.keys())[0])
				self.votosCanciones[method.routing_key][list(lista.keys())[0]]=0 
			
			print ("Inicial",self.votosCanciones)
			
		'''	
		if temporal[0]=="listaActualizada":
			canciones=self.cancionesSitio[method.routing_key]
			votos=self.votosCanciones[method.routing_key]
			songActual=canciones.pop(0)
			del votos[list(songActual.keys())[0]] #elimina la cancion actaul de la lista de votos
			newCanciones,CAMBIO=self.ordenar(canciones,votos)
			newCanciones.insert(0,songActual)
			self.cancionesSitio[dic]=newCanciones
			mensaje=self.listadicc(newCanciones)
			print("Actualizo",mensaje)
			#print (CAMBIO,mensaje)
			if CAMBIO:
				ch.basic_publish(exchange='',
								routing_key=self.SitiosCodigo[method.routing_key],
							
								body=str(mensaje))	
				self.multidifucion(ch,self.mesasSitios[method.routing_key],str(newCanciones))  #difucion a todos, con lista de mesas del sitio y canciones actulizadas
		'''
		if temporal[0]=="terminoCancion":								
			canciones=self.cancionesSitio[method.routing_key].copy()
			votos=self.votosCanciones[method.routing_key].copy()		
			songActual=canciones.pop(0)
			del votos[list(songActual.keys())[0]] #elimina la cancion actaul de la lista de votos
			newCanciones,CAMBIO=self.ordenar(canciones,votos)
			newCanciones.append(songActual)			
			self.votosCanciones[method.routing_key][list(songActual.keys())[0]]=0 #reinicio en 0 votos la cancion terminada
			mensaje=self.listadicc(newCanciones)
			print("TERMINOOOOOOOOOOOOOO")
			self.cancionesSitio[method.routing_key]=newCanciones
			ch.basic_publish(exchange='',
							#routing_key=self.SitiosCodigo[method.routing_key],
							routing_key=self.SitiosCodigo[method.routing_key],
							properties=pika.BasicProperties(delivery_mode=2,),
							body=str(mensaje))
							
			self.multidifucion(ch,self.mesasSitios[method.routing_key],self.ConvertLista(aux))  #difucion a todos, con lista de mesas del sitio y canciones actulizadas							

	def listadicc(self,dic):
		aux=[]
		for lista in dic:
			aux.append(list(lista.keys())[0])
		return aux	
			

	def receiveAtencionMesas(self, ch, method, properties, body):
		body=body.decode("utf-8")
		temporal=body.split(",")
		self.printBox1("Voto recibido de una mesa {}".format(body))	
		self.votosCanciones[temporal[0]][temporal[1]]=self.votosCanciones[temporal[0]][temporal[1]] + 1	
	def receiveMesa(self, ch, method, properties, body):
		print(body)
		body=body.decode("utf-8")
		temporal=body.split(",")
		print(temporal[0])
		self.printBox1("Mensaje recibido de una mesa {}".format(body))
		if temporal[0] in self.mesasSitios:       #verificar si el sitio si exixte, sino vevolver mensaje
			if(not temporal[1] in self.listMesas):
				self.mesasSitios[temporal[0]].append(temporal[1])
				self.listMesas.append(temporal[1])
				ch.basic_publish(exchange='',
								routing_key=properties.reply_to,
							
								body="Correcto")
			print("correcto")

		else:
			ch.basic_publish(exchange='',
							routing_key=properties.reply_to,
						
							body="Error")	
			print(properties.reply_to)				
			print("ERRROR")																		

	def runReceive(self):
		self.channel.start_consuming()


	def runGraph(self):
		self.buttonUpdate.after(1000, self.updatePeriodica)
		self.root.mainloop()
	def multidifucion(self,ch,mesas,canciones):

		for mesa in mesas:
			print(mesa)
			ch.basic_publish(exchange='',
							routing_key=mesa,
						
							body=canciones)				 
	def GenerarCodigo(self):
		string = ""
		while len(string)==0 or string in self.SitiosCodigo:
			string = ""
			chars= 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
			num= 6
			for k in range(num):
				string+=random.choice(chars)
		return string	

	def infocancion(self,dic,song):
		for aux in dic:
			if song in aux:
				return (aux[song])
				


	def ordenar(self,dic,votos):
		resultado=sorted(votos.items(),key=operator.itemgetter(1))
		resultado.reverse()
		newdic=[]
		voll=True
		for a in resultado:
			aux=a[0]
			info=self.infocancion(dic,aux)
			newdic.append({aux:info})
			
		if newdic==dic:
			voll=False    
		return  newdic,voll
	

if __name__ == '__main__':
	servidor=rabbitmqClient()
	hilo1=threading.Thread(target=servidor.runReceive)
	hilo1.start()
	print("Server iniciado")
	
	servidor.runGraph()
	os._exit(1)