from models.constantes import *
import csv
import os

def coolers(cooler:int,valor:int,condicion:bool):
    cooler = cooler + valor if condicion else cooler - valor  
    return cooler 

def suma(a,b):
    suma = a + b
    return suma 

def resta(a,b):
    resta = a - b
    return resta

def set_cero(a):
    a = 0
    return a

def set_color(minutos,segundos):
    if segundos < 30 and minutos < 1:
            color = verde
    elif segundos >= 30:
        color = amarillo
    elif minutos >= 1:
        color = rojo 
    elif minutos >= 2 and segundos > 0:
        color = rojo 
    return color


def anotar_puntaje(nombre, puntaje):
    nombre_archivo = "Score.csv"

    if not os.path.exists(nombre_archivo):
        with open(nombre_archivo, "w", newline='') as archivo:
            escritor_csv = csv.writer(archivo)
            escritor_csv.writerow(['Nombre', 'Puntaje'])
            escritor_csv.writerow([nombre, puntaje])
    else:
        puntajes = leer_puntajes(nombre_archivo)

        if nombre in puntajes and puntajes[nombre] < puntaje:
            puntajes[nombre] = puntaje
        elif nombre not in puntajes:
            puntajes[nombre] = puntaje

        nombres_puntajes = [(nombre, puntajes[nombre]) for nombre in puntajes]

        with open(nombre_archivo, "w", newline='') as archivo:
            escritor_csv = csv.writer(archivo)
            escritor_csv.writerow(['Nombre', 'Puntaje'])
            for nombre, puntaje in nombres_puntajes:
                escritor_csv.writerow([nombre, puntaje])

def leer_puntajes(nombre_archivo):
    puntajes = {}

    with open(nombre_archivo, newline='') as archivo:
        lector_csv = csv.reader(archivo)
        next(lector_csv)  
        for fila in lector_csv:
            if fila:  
                nombre = fila[0]
                if len(fila) > 1:
                    puntaje = int(fila[1])
                else:
                    puntaje = 0  
                puntajes[nombre] = puntaje

    return puntajes

def quick_sort(list):
    if len(list) <= 1:
        return list
    else:
        pivot = list[0][1]
        menores = [(nombre, puntos) for nombre, puntos in list if puntos < pivot]
        iguales = [(nombre, puntos) for nombre, puntos in list if puntos == pivot]
        mayores = [(nombre, puntos) for nombre, puntos in list if puntos > pivot]
        return quick_sort(menores) + iguales + quick_sort(mayores)

def obtener_top3_puntajes(nombre_archivo):
    puntajes = leer_puntajes(nombre_archivo)
    puntajes_ordenados = quick_sort(list(puntajes.items()))[::-1]  

    top3 = puntajes_ordenados[:3]  

    return top3

