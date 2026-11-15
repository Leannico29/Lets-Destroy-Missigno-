"""Proyectiles horizontales del jugador y de los enemigos."""
from __future__ import annotations

from typing import Iterable

import pygame as pg

from game.assets import load_image
from game.settings import WIDTH


class Bullet(pg.sprite.Sprite):
    SIZE = (22, 22)

    def __init__(self, center: tuple[float, float], direction: int, damage: int,
                 sprite: str = "bullet/player.png", speed: float = 480,
                 lifetime: float = 1.2) -> None:
        super().__init__()
        self.direction = 1 if direction >= 0 else -1
        self.damage = damage
        self.speed = speed
        self.lifetime = lifetime
        image = load_image(sprite, self.SIZE)
        self.image = image if self.direction > 0 else pg.transform.flip(image, True, False)
        self.rect = self.image.get_rect(center=(round(center[0]), round(center[1])))
        self._x = float(self.rect.x)

    def update(self, dt: float, solids: Iterable) -> None:
        self.lifetime -= dt
        self._x += self.direction * self.speed * dt
        self.rect.x = round(self._x)
        out_of_screen = self.rect.right < 0 or self.rect.left > WIDTH
        hit_wall = any(self.rect.colliderect(solid.rect) for solid in solids)
        if self.lifetime <= 0 or out_of_screen or hit_wall:
            self.kill()
