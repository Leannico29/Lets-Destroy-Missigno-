"""Elementos estáticos del nivel: plataformas, trampas y frutas."""
from __future__ import annotations

import pygame as pg

from game.assets import load_frames, load_image


class Platform(pg.sprite.Sprite):
    """Bloque sólido: no se puede atravesar desde ningún lado."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        super().__init__()
        self.image = load_image("tiles/platform.png", (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))


class Trap(pg.sprite.Sprite):
    DAMAGE = 25

    def __init__(self, x: int, y: int, size: int = 30) -> None:
        super().__init__()
        self.image = load_image("traps/spikes.png", (size, size))
        self.rect = self.image.get_rect(topleft=(x, y))
        # La zona que lastima es un poco más chica que el dibujo, para que
        # rozar el borde de un pincho no cuente como golpe.
        self.hitbox = self.rect.inflate(-size // 4, -size // 3).move(0, size // 6)


class Fruit(pg.sprite.Sprite):
    SCORE = 500
    FRAME_TIME = 0.05
    SPRITES = {"apple": "fruit/apple.png", "banana": "fruit/bananas.png"}

    def __init__(self, x: int, y: int, kind: str = "apple", size: int = 40) -> None:
        super().__init__()
        self.frames = load_frames(self.SPRITES[kind], 17, size=(size, size))
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self._timer = 0.0
        self._index = 0

    def update(self, dt: float) -> None:
        self._timer += dt
        if self._timer >= self.FRAME_TIME:
            self._timer = 0.0
            self._index = (self._index + 1) % len(self.frames)
            self.image = self.frames[self._index]
