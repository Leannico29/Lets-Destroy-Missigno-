import pygame as pg
from models.constantes import ANCHO_VENTANA, LARGO_VENTANA

class Plataforma:
    def __init__(self, x, y, ancho, largo):
        self.imagen = pg.image.load('models\plataformas\platform.png')
        self.imagen = pg.transform.scale(self.imagen, (ancho, largo))
        self.rect = self.imagen.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.rect_colision_superior = pg.Rect(self.rect.x, self.rect.y, self.rect.width, 10)
        self.rect_colision_inferior = pg.Rect(self.rect.x, self.rect.y + self.rect.height - 10, self.rect.width, 10)
        self.rect_colision_izquierda = pg.Rect(self.rect.x, self.rect.y, 10, self.rect.height)
        self.rect_colision_derecha = pg.Rect(self.rect.x + self.rect.width - 10, self.rect.y, 10, self.rect.height)

    def draw(self, screen):
        screen.blit(self.imagen, self.rect)

