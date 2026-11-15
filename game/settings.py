"""Configuración global: ventana, rutas, física y paleta de colores."""
from pathlib import Path

TITLE = "Let's Destroy Missigno"
WIDTH, HEIGHT = 800, 600
FPS = 60
# Si un frame tarda mucho (por ejemplo al arrastrar la ventana) se limita el
# paso de simulación para que nada atraviese plataformas.
MAX_FRAME_TIME = 0.025

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
MUSIC_DIR = ASSETS_DIR / "music"
SCORES_FILE = BASE_DIR / "scores.csv"

# Física, en píxeles por segundo (y por segundo al cuadrado).
GRAVITY = 1800
MAX_FALL_SPEED = 800

DEFAULT_VOLUME = 0.3

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (150, 255, 155)
YELLOW = (255, 230, 60)
RED = (255, 70, 70)
ORANGE = (255, 155, 0)
DARK_OVERLAY = (0, 0, 0, 150)
