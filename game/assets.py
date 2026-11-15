"""Carga de imágenes, spritesheets y audio.

Las imágenes se cachean para no leer el mismo archivo del disco cada vez que
aparece un enemigo o una fruta. El audio es opcional: si falta un archivo o la
PC no tiene dispositivo de sonido, el juego sigue funcionando en silencio.
"""
from __future__ import annotations

import logging
from functools import lru_cache

import pygame as pg

from game.settings import DEFAULT_VOLUME, IMAGES_DIR, MUSIC_DIR

log = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def load_image(relative_path: str, size: tuple[int, int] | None = None) -> pg.Surface:
    """Carga una imagen de assets/images, opcionalmente escalada."""
    surface = pg.image.load(str(IMAGES_DIR / relative_path))
    if pg.display.get_surface() is not None:
        surface = surface.convert_alpha()
    if size is not None:
        surface = pg.transform.scale(surface, size)
    return surface


@lru_cache(maxsize=None)
def load_frames(
    relative_path: str,
    columns: int,
    rows: int = 1,
    size: tuple[int, int] | None = None,
) -> tuple[pg.Surface, ...]:
    """Corta un spritesheet en frames del mismo tamaño (de izquierda a derecha)."""
    sheet = load_image(relative_path)
    frame_w, frame_h = sheet.get_width() // columns, sheet.get_height() // rows
    frames = []
    for row in range(rows):
        for col in range(columns):
            frame = sheet.subsurface((col * frame_w, row * frame_h, frame_w, frame_h))
            if size is not None:
                frame = pg.transform.scale(frame, size)
            frames.append(frame)
    return tuple(frames)


def flip_frames(frames: tuple[pg.Surface, ...]) -> tuple[pg.Surface, ...]:
    return tuple(pg.transform.flip(frame, True, False) for frame in frames)


class Audio:
    """Música de fondo y efectos con volumen y mute centralizados."""

    def __init__(self, volume: float = DEFAULT_VOLUME) -> None:
        self.volume = volume
        self.muted = False
        self.enabled = pg.mixer.get_init() is not None
        self._current_track: str | None = None
        self._sounds: dict[str, pg.mixer.Sound | None] = {}
        if not self.enabled:
            log.info("Sin dispositivo de audio: el juego corre en silencio.")

    @property
    def effective_volume(self) -> float:
        return 0.0 if self.muted else self.volume

    def play_music(self, filename: str) -> None:
        if not self.enabled or filename == self._current_track:
            return
        path = MUSIC_DIR / filename
        if not path.exists():
            log.info("Música no encontrada, se omite: %s", path.name)
            pg.mixer.music.stop()
            self._current_track = None
            return
        try:
            pg.mixer.music.load(str(path))
            pg.mixer.music.set_volume(self.effective_volume)
            pg.mixer.music.play(-1)
            self._current_track = filename
        except pg.error as exc:
            log.warning("No se pudo reproducir %s: %s", path.name, exc)

    def play_sound(self, filename: str) -> None:
        if not self.enabled:
            return
        if filename not in self._sounds:
            path = MUSIC_DIR / filename
            try:
                self._sounds[filename] = pg.mixer.Sound(str(path)) if path.exists() else None
            except pg.error as exc:
                log.warning("No se pudo cargar %s: %s", path.name, exc)
                self._sounds[filename] = None
        sound = self._sounds[filename]
        if sound is not None:
            sound.set_volume(self.effective_volume)
            sound.play()

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        if self.enabled:
            pg.mixer.music.set_volume(self.effective_volume)
