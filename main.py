#!/usr/bin/python3

import logging
import time
import sys
import re
import telebot
from telebot import types
import requests
import sqlite3 as sq
import argparse
import os
from datetime import date, timedelta
import time

from CONSTANTS import BIENVENIDA
from CONSTANTS import KEY

# --------------------------------------------------------------------------- #

# LOGGING
logging.basicConfig(  # filename="/home/pi/cocina.log",
		filemode='w', level=logging.WARNING)

# --------------------------------------------------------------------------- #

# FECHA Y HORA
fecha = str(date.today())
hora = str(time.strftime('%H'))

# --------------------------------------------------------------------------- #

# INSTANCIA CLASE TELEBOT
bot = telebot.TeleBot('324536212:AAEi5lmk0NWuQU0tkV0TmRH-WuPIyWrLswg')

# DESECHA LOS COMANDOS CUANDO EL BOT NO ESTÁ ACTIVO
bot.skip_pending = False


# --------------------------------------------------------------------------- #

# FUNCIÓN QUE QUITA LAS TILDES AL STRING QUE SE LE PASA COMO ARGUMENTO
def quita_acentos(cadena):
	try:
		if 'á' in cadena:
			cadena = cadena.replace('á', 'a')
		if 'é' in cadena:
			cadena = cadena.replace('é', 'e')
		if 'í' in cadena:
			cadena = cadena.replace('í', 'i')
		if 'ó' in cadena:
			cadena = cadena.replace('ó', 'o')
		if 'ú' in cadena:
			cadena = cadena.replace('ú', 'u')
		return cadena
	except:
		logging.exception('   Error en la función quita_acentos\n\n')


# --------------------------------------------------------------------------- #

# COMPRUEBA SI LA CLAVE INTRODUCIDA ES CORRECTA
def comprobar_clave(mensaje):
	try:
		clave = mensaje.text
		user = mensaje.chat.username
		
		if user is None:
			user = 'vacio'
		
		nombre = mensaje.chat.first_name
		
		if nombre is None:
			nombre = 'vacio'
		chat_id = mensaje.chat.id
		
		if clave == KEY:
			registro_usuario(nombre, user, chat_id)
			bot.send_message(chat_id, '✅  %s, Has sido dado de alta '
			                          'correctamente' % nombre)
		else:
			bot.send_message(chat_id, '⛔ CLAVE INCORRECTA ⛔')
			start(mensaje)
	except:
		logging.exception('   Error en la función "comprobar_clave"\n\n')


# --------------------------------------------------------------------------- #

# COMPRUEBA SI EL USUARIO ESTÁ DADO DE ALTA EN LA BASE DE DATOS
def comprueba_usuario(chatid):
	try:
		conexion = sq.connect('/home/pi/cocina/database/usuarios.bd')
		cursor = conexion.cursor()
		tabla = "SELECT ids FROM user"
		if cursor.execute(tabla):
			filas = cursor.fetchall()
			for fila in filas:
				if str(chatid) in str(fila):
					esta = True
					
					return esta
	except:
		logging.exception('  Error en la función comprueba usuario\n\n')


# --------------------------------------------------------------------------- #

# AGREGA UN USUARIO A LA BASE DE DATOS
def registro_usuario(nombre, usuario, ids):
	try:
		conect = sq.connect('/home/pi/cocina/database/usuarios.bd')
		cursor = conect.cursor()
		
		usuarios = """CREATE TABLE IF NOT EXISTS user(
					id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
					fecha INT NOT NULL,
					hora INT NOT NULL,
					nombre CHAR NOT NULL,
					usuario CHAR NOT NULL,
					ids INT NOT NULL)"""
		
		cursor.execute(usuarios)
		datos = (fecha, hora, nombre, usuario, ids)
		
		usuarios = """INSERT INTO user(
					fecha,
					hora,
					nombre,
					usuario,
					ids)
					VALUES(?,?,?,?,?)
				"""
		cursor.execute(usuarios, datos)
		cursor.close()
		conect.commit()
		conect.close()
	except:
		logging.exception('   Error en la función registro_usuario\n\n')


# --------------------------------------------------------------------------- #

# BUSCA EN LA BASE DE DATOS VACIO
def busca_vacio(mensaje):
	try:
		chat_id = mensaje.chat.id
		busqueda = mensaje.text
		conect = sq.connect('/home/pi/cocina/database/bd_vacio.sql')
		cursor = conect.cursor()
		tabla = "SELECT * FROM vacio"
		
		if cursor.execute(tabla):
			filas = cursor.fetchall()
			for fila in filas:
				alimento = fila[1]
				temperatura = fila[2]
				tiempo = fila[3]
				if busqueda in str(fila[1]):
					bot.send_message(chat_id, alimento.upper() + '\n\n' + str(
						'🌡    ') + str(temperatura) + 'º\n\n' + str('⌛     ') +
					                 str(tiempo))
					time.sleep(.5)
			teclado_principal(mensaje)
	except:
		logging.exception('Error en la función busca_vacio')


# --------------------------------------------------------------------------- #

# FUNCIÓN QUE QUITA EL TECLADO BOTONES Y MUESTRA EL DE TEXTO
def quita_teclado(chat_id):
	try:
		markup = types.ReplyKeyboardRemove(selective=False)
		bot.send_message(chat_id, '👍', reply_markup=markup)
	except:
		logging.exception('   Error en la función quita_teclado\n\n')


# --------------------------------------------------------------------------- #

# TECLADO PRINCIPAL
def teclado_principal(mensaje):
	chat_id = mensaje.chat.id
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
	                                   one_time_keyboard=False)
	markup.add('🍳    RECETAS', '📠    AL VACÍO')
	markup.add('🗓    LISTAS', '⬅    SALIR')
	markup.Remove_keyboard = True
	msg = bot.send_message(chat_id, '👍', reply_markup=markup)
	bot.register_next_step_handler(msg, process_teclado_principal)


# --------------------------------------------------------------------------- #

# PROCESA EL TECLADO PRINCIPAL
def process_teclado_principal(mensaje):
	men = mensaje.text
	chat_id = mensaje.chat.id
	
	if men == '🍳    RECETAS':
		with open('/home/pi/cocina/recetas/plantilla.txt', 'r') as receta:
			r = receta.read()
			bot.send_message(chat_id, r)
	if men == '📠    AL VACÍO':
		quita_teclado(chat_id)
		msg = bot.send_message(chat_id, '🔍   Escribe el alimento a buscar...')
		bot.register_next_step_handler(msg, busca_vacio)
	if men == '🗓    LISTAS':
		teclado_listas(mensaje)
	if men == '⬅   SALIR':
		print('salir')


# --------------------------------------------------------------------------- #

# FUNCIÓN START, OBTIENE DATOS DE USUARIO
@bot.message_handler(commands=['start'])
def start(mensaje):
	try:
		chat_id = mensaje.chat.id
		user = mensaje.chat.username
		nombre = mensaje.chat.first_name
		# Si el usuario no ha añadido el first_name (nombre),
		# toma como valor "vacio" para evitar fallos al retornar None
		if user is None:
			user = 'vacio'
		
		if comprueba_usuario(chat_id) is True:
			bot.send_message(chat_id, '🤘  Hola ' + nombre.upper())
			teclado_principal(mensaje)
		else:
			msg = bot.reply_to(mensaje, '🗝  Introduce la clave para '
			                            'continuar ...')
			bot.register_next_step_handler(msg, comprobar_clave)
	except:
		logging.exception('   Error en la función start\n\n')


# --------------------------------------------------------------------------- #

# TECLADO LISTAS
def teclado_listas(mensaje):
	chat_id = mensaje.chat.id
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
	                                   one_time_keyboard=False)
	markup.add('🔥  PRODUCCIÓN CALIENTE')
	markup.add('❄  PRODUCCIÓN FRiO')
	markup.add('🔥  MISE IN PLACE CALIENTE')
	markup.add('❄  MISE IN PLACE FRIO')
	markup.Remove_keyboard = True
	msg = bot.send_message(chat_id, '👍', reply_markup=markup)
	bot.register_next_step_handler(msg, process_teclado_listas)


# --------------------------------------------------------------------------- #

# PROCESA TECLADO LISTAS
def process_teclado_listas(mensaje):
	men = mensaje.text
	chat_id = mensaje.chat.id
	
	if men == '🔥  PRODUCCIÓN CALIENTE':
		with open('/home/pi/cocina/recetas/listas/prod_caliente.txt', 'r') as \
				a:
			r = a.read()
			bot.send_message(chat_id, r)

# --------------------------------------------------------------------------- #


logging.warning('   Se ha iniciado el bot a las %s horas\n\n' % hora)

bot.polling()
