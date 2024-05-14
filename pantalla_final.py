import pygame as pg
import sys
import os
import csv
from defs_auxiliares import *
from models.botones.botones import Botones


#def pantalla_final(volumen):
volumen = 0.3
screen = pg.display.set_mode((ANCHO_VENTANA, LARGO_VENTANA))
pg.init()
back_img = pg.image.load('models\\backgrounds\\fondo_menu.jpeg') 
back_img =  pg.transform.scale(back_img,(ANCHO_VENTANA, LARGO_VENTANA))
pg.display.set_caption('Pantalla Final')
pg.mixer.music.load('music/musica_menu_1.wav')
pg.mixer.music.set_volume(volumen)
pg.mixer.music.play(-1)

nombre_archivo = "Score.csv"
top3_puntajes = obtener_top3_puntajes(nombre_archivo)

font = pg.font.Font(None, 36)
color_texto = (255, 255, 255)
x = 50
y = 100
separacion = 50
boton_start = Botones((ANCHO_VENTANA * 0.1),(LARGO_VENTANA // 2),'models\\botones\Text_Play_Button.png',2)
boton_exit = Botones((ANCHO_VENTANA * 0.65),(LARGO_VENTANA // 2),'models\\botones\Text_Exit_Button.png',2)
boton_mute = Botones((ANCHO_VENTANA * 0.47),(((LARGO_VENTANA * 0.6) + 130)),'models\\botones\Sound_Off_Button.png',1.5)


running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
    screen.blit(back_img, back_img.get_rect())  
    texto_titulo = font.render('Top 3 Puntajes', True, color_texto)
    screen.blit(texto_titulo, (300, 50))

    for i, (nombre, puntaje) in enumerate(top3_puntajes):
        texto_nombre = font.render(f'{i+1}. {nombre}', True, color_texto)
        screen.blit(texto_nombre, (x, y + i * separacion))

    if boton_start.update():
        pg.mixer.music.stop()
        menu = False

    if boton_exit.update():
        pg.quit()

    if boton_mute.update():
        if volumen == 0.3:
            volumen = 0
            pg.mixer.music.set_volume(volumen) 
        else:
            volumen = 0.3
            pg.mixer.music.set_volume(volumen) 

    boton_start.draw(screen)       
    boton_exit.draw(screen)        
    boton_mute.draw(screen)

    texto_puntaje = font.render(str(puntaje), True, color_texto)
    screen.blit(texto_puntaje, (x + 200, y + i * separacion))

    pg.display.flip()

pg.quit()