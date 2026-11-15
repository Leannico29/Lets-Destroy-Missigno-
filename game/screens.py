"""Pantallas fuera del juego: menú principal, ingreso de nombre y resultados."""
from __future__ import annotations

from enum import Enum, auto

import pygame as pg

from game.assets import Audio, load_image
from game.settings import BLACK, FPS, GREEN, HEIGHT, ORANGE, RED, TITLE, WHITE, WIDTH
from game.ui import Button, Fonts, draw_text

MENU_MUSIC = "musica_menu_1.wav"
NAME_MUSIC = "ambiente.wav"
NAME_MIN, NAME_MAX = 2, 8


class Choice(Enum):
    PLAY = auto()
    BACK = auto()
    QUIT = auto()


class Screens:
    def __init__(self, screen: pg.Surface, clock: pg.time.Clock, audio: Audio, fonts: Fonts) -> None:
        self.screen = screen
        self.clock = clock
        self.audio = audio
        self.fonts = fonts

    def main_menu(self) -> Choice:
        self.audio.play_music(MENU_MUSIC)
        background = load_image("backgrounds/fondo_menu.jpeg", (WIDTH, HEIGHT))
        play = Button("Text_Play_Button.png", (WIDTH // 4, HEIGHT // 2 + 30), hotkey=pg.K_RETURN)
        leave = Button("Text_Exit_Button.png", (WIDTH * 3 // 4, HEIGHT // 2 + 30), hotkey=pg.K_ESCAPE)
        mute = Button("Sound_Off_Button.png", (WIDTH // 2, HEIGHT - 80), scale=1.5, hotkey=pg.K_m)

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT or leave.clicked(event):
                    return Choice.QUIT
                if play.clicked(event):
                    return Choice.PLAY
                if mute.clicked(event):
                    self.audio.toggle_mute()

            self.screen.blit(background, (0, 0))
            draw_text(self.screen, self.fonts.title, TITLE, WHITE, center=(WIDTH // 2, 120))
            draw_text(self.screen, self.fonts.normal, "¡Salvanos de los glitches!", ORANGE,
                      center=(WIDTH // 2, 175))
            for button in (play, leave, mute):
                button.draw(self.screen)
            sound = "Sonido: apagado" if self.audio.muted else "Sonido: encendido"
            draw_text(self.screen, self.fonts.small, sound, WHITE, center=(WIDTH // 2, HEIGHT - 40))
            draw_text(self.screen, self.fonts.small,
                      "Flechas/AD: mover  ·  Shift: correr  ·  Espacio: saltar  ·  Q: disparar  ·  Esc: pausa",
                      WHITE, center=(WIDTH // 2, HEIGHT // 2 + 110))
            pg.display.flip()
            self.clock.tick(FPS)

    def ask_name(self) -> str | None:
        """Devuelve el nombre ingresado, o None si el jugador vuelve o cierra."""
        self.audio.play_music(NAME_MUSIC)
        background = load_image("backgrounds/fondo_nombre.jpg", (WIDTH, HEIGHT))
        portrait = load_image("player/fall.png", (130, 130))
        name = ""
        pg.key.start_text_input()
        try:
            while True:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return None
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            return ""
                        if event.key in (pg.K_RETURN, pg.K_KP_ENTER) and len(name.strip()) >= NAME_MIN:
                            return name.strip()
                        if event.key == pg.K_BACKSPACE:
                            name = name[:-1]
                    elif event.type == pg.TEXTINPUT:
                        allowed = "".join(c for c in event.text if c.isalnum() or c in " _-")
                        name = (name + allowed)[:NAME_MAX]

                self.screen.blit(background, (0, 0))
                draw_text(self.screen, self.fonts.normal, "¿Cómo te gustaría que te llamemos?", BLACK,
                          shadow=False, center=(WIDTH // 2, HEIGHT // 2 - 120))
                box = pg.Rect(0, 0, 260, 48)
                box.center = (WIDTH // 2, HEIGHT // 2 - 50)
                pg.draw.rect(self.screen, WHITE, box, border_radius=8)
                pg.draw.rect(self.screen, BLACK, box, 2, border_radius=8)
                cursor = "_" if pg.time.get_ticks() // 400 % 2 else " "
                draw_text(self.screen, self.fonts.normal, name + cursor, BLACK, shadow=False,
                          center=box.center)
                hint = "Enter para empezar  ·  Esc para volver"
                if 0 < len(name.strip()) < NAME_MIN:
                    hint = f"Mínimo {NAME_MIN} caracteres"
                draw_text(self.screen, self.fonts.small, hint, BLACK, shadow=False,
                          center=(WIDTH // 2, box.bottom + 22))
                self.screen.blit(portrait, portrait.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 110)))
                pg.display.flip()
                self.clock.tick(FPS)
        finally:
            pg.key.stop_text_input()

    def results(self, name: str, score: int, won: bool, ranking: list[tuple[str, int]]) -> Choice:
        self.audio.play_music(MENU_MUSIC)
        background = load_image("backgrounds/fondo_menu.jpeg", (WIDTH, HEIGHT))
        again = Button("Text_Play_Button.png", (WIDTH // 4, HEIGHT - 110), hotkey=pg.K_RETURN)
        leave = Button("Text_Exit_Button.png", (WIDTH * 3 // 4, HEIGHT - 110), hotkey=pg.K_ESCAPE)

        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT or leave.clicked(event):
                    return Choice.QUIT
                if again.clicked(event):
                    return Choice.PLAY

            self.screen.blit(background, (0, 0))
            title, color = ("¡Derrotaste a Missigno!", GREEN) if won else ("Game over", RED)
            draw_text(self.screen, self.fonts.large, title, color, center=(WIDTH // 2, 70))
            draw_text(self.screen, self.fonts.normal, f"{name}: {score} puntos", ORANGE,
                      center=(WIDTH // 2, 125))
            draw_text(self.screen, self.fonts.normal, "Mejores puntajes", WHITE, center=(WIDTH // 2, 185))
            for position, (player, points) in enumerate(ranking, start=1):
                y = 225 + (position - 1) * 40
                highlight = ORANGE if player == name else WHITE
                draw_text(self.screen, self.fonts.normal, f"{position}. {player}", highlight,
                          midleft=(WIDTH // 2 - 140, y))
                draw_text(self.screen, self.fonts.normal, str(points), highlight,
                          midright=(WIDTH // 2 + 140, y))
            for button in (again, leave):
                button.draw(self.screen)
            pg.display.flip()
            self.clock.tick(FPS)
