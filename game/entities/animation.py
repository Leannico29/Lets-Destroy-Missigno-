"""Reproductor de animaciones por nombre, con frames para mirar a cada lado."""
from __future__ import annotations

import pygame as pg

from game.assets import flip_frames

Frames = tuple[pg.Surface, ...]


class Animator:
    def __init__(self, animations: dict[str, Frames], frame_time: float = 0.08,
                 faces_right: bool = True) -> None:
        """`faces_right` indica hacia dónde mira el spritesheet original."""
        right = animations if faces_right else {k: flip_frames(v) for k, v in animations.items()}
        self._frames = {
            1: right,
            -1: {name: flip_frames(frames) for name, frames in right.items()},
        }
        self.frame_time = frame_time
        self.name = next(iter(animations))
        self.index = 0
        self.loop = True
        self.finished = False
        self._timer = 0.0

    def play(self, name: str, loop: bool = True) -> None:
        if name != self.name:
            self.name = name
            self.index = 0
            self._timer = 0.0
            self.finished = False
        self.loop = loop

    def update(self, dt: float) -> None:
        total = len(self._frames[1][self.name])
        self._timer += dt
        while self._timer >= self.frame_time:
            self._timer -= self.frame_time
            if self.index < total - 1:
                self.index += 1
            elif self.loop:
                self.index = 0
            else:
                self.finished = True

    def image(self, facing: int) -> pg.Surface:
        return self._frames[facing][self.name][self.index]
