"""Cuerpo físico compartido por el jugador y los enemigos.

Las colisiones se resuelven primero en el eje X y después en el Y. Así una
pared frena el avance lateral y un techo corta el salto, en lugar de
"teletransportar" al personaje arriba de la plataforma como pasaba antes.
"""
from __future__ import annotations

from typing import Iterable, Protocol

import pygame as pg

from game.settings import GRAVITY, MAX_FALL_SPEED, WIDTH


class Solid(Protocol):
    rect: pg.Rect


class PhysicsBody(pg.sprite.Sprite):
    def __init__(self, x: float, y: float, width: int, height: int) -> None:
        super().__init__()
        self.rect = pg.Rect(round(x), round(y), width, height)
        # La posición real se guarda en floats para que el movimiento no
        # dependa de los FPS ni pierda decimales al redondear al rect.
        self.pos = pg.Vector2(x, y)
        self.velocity = pg.Vector2()
        self.on_ground = False
        self.blocked_side = 0  # -1 pared a la izquierda, 1 a la derecha, 0 libre

    def place(self, x: float, y: float) -> None:
        self.pos.update(x, y)
        self.rect.topleft = (round(x), round(y))
        self.velocity.update(0, 0)

    def apply_physics(self, dt: float, solids: Iterable[Solid]) -> None:
        solids = list(solids)
        self.velocity.y = min(self.velocity.y + GRAVITY * dt, MAX_FALL_SPEED)
        self._move_x(self.velocity.x * dt, solids)
        self._move_y(self.velocity.y * dt, solids)
        if self.velocity.y >= 0:
            self.on_ground = self._touching_ground(solids)

    def _move_x(self, dx: float, solids: list[Solid]) -> None:
        self.blocked_side = 0
        self.pos.x += dx
        self.rect.x = round(self.pos.x)
        for solid in solids:
            if not self.rect.colliderect(solid.rect):
                continue
            if dx > 0:
                self.rect.right = solid.rect.left
                self.blocked_side = 1
            elif dx < 0:
                self.rect.left = solid.rect.right
                self.blocked_side = -1
            self.pos.x = self.rect.x

        if self.rect.left < 0:
            self.rect.left = 0
            self.blocked_side = -1
        elif self.rect.right > WIDTH:
            self.rect.right = WIDTH
            self.blocked_side = 1
        self.pos.x = self.rect.x

    def _move_y(self, dy: float, solids: list[Solid]) -> None:
        self.on_ground = False
        self.pos.y += dy
        self.rect.y = round(self.pos.y)
        for solid in solids:
            if not self.rect.colliderect(solid.rect):
                continue
            if dy > 0:
                self.rect.bottom = solid.rect.top
                self.on_ground = True
            elif dy < 0:
                self.rect.top = solid.rect.bottom
            self.velocity.y = 0
            self.pos.y = self.rect.y

        if self.rect.top < 0:
            self.rect.top = 0
            self.velocity.y = max(self.velocity.y, 0)
            self.pos.y = self.rect.y

    def _touching_ground(self, solids: list[Solid]) -> bool:
        probe = self.rect.move(0, 1)
        return any(probe.colliderect(solid.rect) for solid in solids)
