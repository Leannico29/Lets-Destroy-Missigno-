"""Flujo general: menú -> nombre -> niveles -> resultados, en una sola ventana.

El código original encadenaba pantallas llamando una función dentro de otra
(menú -> nombre -> nivel 1 -> nivel 2...), así que cada partida apilaba bucles
y al cerrar un nivel se volvía al anterior. Acá cada pantalla devuelve un
resultado y este módulo decide qué sigue.
"""
from __future__ import annotations

import pygame as pg

from game.assets import Audio
from game.level import Level, Outcome
from game.levels import LEVELS
from game.scores import save_score, top_scores
from game.screens import Choice, Screens
from game.settings import HEIGHT, TITLE, WIDTH
from game.ui import Fonts


class Game:
    def __init__(self) -> None:
        pg.init()
        pg.display.set_caption(TITLE)
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.audio = Audio()
        self.fonts = Fonts()
        self.screens = Screens(self.screen, self.clock, self.audio, self.fonts)

    def run(self) -> None:
        try:
            while self.screens.main_menu() is Choice.PLAY:
                name = self.screens.ask_name()
                if name is None:
                    break
                if name and not self.play_session(name):
                    break
        finally:
            pg.quit()

    def play_session(self, name: str) -> bool:
        """Juega todos los niveles. Devuelve False si el jugador cerró la ventana."""
        score = 0
        won = True
        for level_data in LEVELS:
            level = Level(level_data, self.screen, self.clock, self.audio, self.fonts, score=score)
            outcome = level.run()
            score = level.score
            if outcome is Outcome.QUIT:
                return False
            if outcome is Outcome.FAILED:
                won = False
                break
        save_score(name, score)
        return self.screens.results(name, score, won, top_scores(3)) is Choice.PLAY
