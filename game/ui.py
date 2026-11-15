"""Componentes de interfaz: botones, textos y HUD."""
from __future__ import annotations

import pygame as pg

from game.assets import load_image
from game.settings import BLACK, DARK_OVERLAY, GREEN, HEIGHT, RED, WHITE, WIDTH, YELLOW


class Fonts:
    def __init__(self) -> None:
        self.small = pg.font.Font(None, 24)
        self.normal = pg.font.Font(None, 34)
        self.large = pg.font.Font(None, 56)
        self.title = pg.font.Font(None, 72)


class Button:
    """Botón con imagen que se activa al soltar el clic encima (o con su tecla)."""

    def __init__(self, image: str, center: tuple[int, int], scale: float = 2.0,
                 hotkey: int | None = None) -> None:
        base = load_image(f"ui/{image}")
        size = (round(base.get_width() * scale), round(base.get_height() * scale))
        self.image = pg.transform.scale(base, size)
        self.hover_image = self.image.copy()
        self.hover_image.fill((40, 40, 40), special_flags=pg.BLEND_RGB_ADD)
        self.rect = self.image.get_rect(center=center)
        self.hotkey = hotkey

    def clicked(self, event: pg.event.Event) -> bool:
        if event.type == pg.MOUSEBUTTONUP and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return event.type == pg.KEYDOWN and self.hotkey is not None and event.key == self.hotkey

    def draw(self, surface: pg.Surface) -> None:
        hovered = self.rect.collidepoint(pg.mouse.get_pos())
        surface.blit(self.hover_image if hovered else self.image, self.rect)


def draw_text(surface: pg.Surface, font: pg.font.Font, text: str, color=WHITE, *,
              shadow: bool = True, **position) -> pg.Rect:
    """Dibuja texto con sombra; `position` acepta center=, topleft=, midtop=, etc."""
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(**position)
    if shadow:
        surface.blit(font.render(text, True, BLACK), rect.move(2, 2))
    surface.blit(rendered, rect)
    return rect


def draw_overlay(surface: pg.Surface) -> None:
    overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
    overlay.fill(DARK_OVERLAY)
    surface.blit(overlay, (0, 0))


def health_color(ratio: float) -> tuple[int, int, int]:
    if ratio > 0.6:
        return GREEN
    if ratio > 0.3:
        return YELLOW
    return RED


def draw_bar(surface: pg.Surface, rect: pg.Rect, ratio: float, color) -> None:
    pg.draw.rect(surface, BLACK, rect.inflate(4, 4), border_radius=4)
    pg.draw.rect(surface, (60, 60, 60), rect, border_radius=3)
    filled = rect.copy()
    filled.width = round(rect.width * max(0.0, min(1.0, ratio)))
    if filled.width:
        pg.draw.rect(surface, color, filled, border_radius=3)
