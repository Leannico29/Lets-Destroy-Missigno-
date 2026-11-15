"""Definición de los niveles como datos.

Antes cada nivel era un archivo de ~350 líneas con el mismo bucle copiado.
Ahora un nivel es solo su diseño; `game.level.Level` sabe jugar cualquiera.
"""
from __future__ import annotations

from dataclasses import dataclass, field

Rect = tuple[int, int, int, int]
Point = tuple[int, int]

GROUND: Rect = (0, 530, 800, 70)
BLOCK = 75


@dataclass(frozen=True)
class EnemySpawn:
    x: int
    y: int
    boss: bool = False
    speed: float = 70
    max_health: int = 100
    respawns: int = 0
    can_shoot: bool = True


@dataclass(frozen=True)
class FruitSpawn:
    x: int
    y: int
    kind: str = "apple"


@dataclass(frozen=True)
class LevelData:
    name: str
    background: str
    music: str
    time_limit: int
    player_start: Point
    player_health: int
    platforms: tuple[Rect, ...]
    traps: tuple[Point, ...] = ()
    fruits: tuple[FruitSpawn, ...] = ()
    enemies: tuple[EnemySpawn, ...] = field(default_factory=tuple)


# Escenario compartido por los niveles 2 y 3: una escalera de bloques hasta
# la parte alta de la derecha, con escalones finos para que todo sea alcanzable.
TOWER_LAYOUT: tuple[Rect, ...] = (
    GROUND,
    (0, 455, BLOCK, BLOCK), (75, 455, BLOCK, BLOCK),
    (450, 455, BLOCK, BLOCK), (450, 380, BLOCK, BLOCK),
    (525, 455, BLOCK, BLOCK), (525, 380, BLOCK, BLOCK),
    (525, 305, BLOCK, BLOCK), (525, 230, BLOCK, BLOCK),
    (600, 230, BLOCK, BLOCK), (725, 380, BLOCK, BLOCK),
    (330, 445, 70, 24),   # escalón: piso -> columna izquierda
    (400, 300, 60, 24),   # escalón: columna izquierda -> torre
)
TOWER_TRAPS: tuple[Point, ...] = (
    (150, 500), (180, 500), (0, 425), (420, 500), (570, 200), (600, 200), (497, 350),
)
TOWER_FRUITS = (FruitSpawn(640, 490, "banana"), FruitSpawn(745, 340, "apple"))


LEVELS: tuple[LevelData, ...] = (
    LevelData(
        name="Nivel 1",
        background="backgrounds/fondo.jpeg",
        music="musica-niveles_2.wav",
        time_limit=90,
        player_start=(70, 420),
        player_health=100,
        platforms=(
            GROUND,
            (0, 455, BLOCK, BLOCK), (75, 455, BLOCK, BLOCK),
            (200, 255, 400, 50),
            (525, 455, BLOCK, BLOCK), (525, 380, BLOCK, BLOCK), (525, 305, BLOCK, BLOCK),
            (110, 360, 70, 24),   # escalón para subir a la plataforma larga
        ),
        traps=((0, 425), (30, 425), (260, 225), (290, 225), (320, 225)),
        fruits=(FruitSpawn(640, 490, "banana"), FruitSpawn(265, 175, "apple")),
        # Enemigo cuerpo a cuerpo que reaparece una vez: hay que vencerlo dos veces.
        enemies=(EnemySpawn(420, 200, speed=80, respawns=1, can_shoot=False),),
    ),
    LevelData(
        name="Nivel 2",
        background="backgrounds/fondo_2.jpeg",
        music="ambiente.wav",
        time_limit=100,
        player_start=(50, 420),
        player_health=100,
        platforms=TOWER_LAYOUT,
        traps=TOWER_TRAPS,
        fruits=TOWER_FRUITS,
        enemies=(
            EnemySpawn(250, 480, speed=65),
            EnemySpawn(650, 480, speed=75),
            EnemySpawn(530, 150, speed=50),  # vigía en lo alto de la torre
        ),
    ),
    LevelData(
        name="Nivel final",
        background="backgrounds/fondo_3.jpg",
        music="musica_nvl.wav",
        time_limit=150,
        player_start=(50, 420),
        player_health=200,
        platforms=TOWER_LAYOUT,
        traps=TOWER_TRAPS,
        fruits=TOWER_FRUITS,
        enemies=(EnemySpawn(240, 300, boss=True),),
    ),
)
