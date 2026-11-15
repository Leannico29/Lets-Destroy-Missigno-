"""Enemigos con IA basada en una máquina de estados.

Estados del enemigo común:
    PATROL  camina por su plataforma y se da vuelta ante paredes, bordes o trampas.
    PAUSE   se queda quieto un momento (le da variedad a la patrulla).
    CHASE   ve al jugador: lo encara, se acerca sin tirarse al vacío y dispara.
    SEARCH  perdió de vista al jugador y va hasta el último lugar donde lo vio.

El jefe (Missigno) reutiliza esa lógica y agrega saltos, una fase de furia al
quedar con media vida y "glitches" que lo teletransportan por el escenario.
"""
from __future__ import annotations

import random
from enum import Enum, auto
from typing import Iterable, Sequence

import pygame as pg

from game.assets import load_frames
from game.entities.animation import Animator
from game.entities.bullet import Bullet
from game.entities.physics import PhysicsBody
from game.settings import GREEN, HEIGHT, RED, WIDTH


class State(Enum):
    PATROL = auto()
    PAUSE = auto()
    CHASE = auto()
    SEARCH = auto()


class Enemy(PhysicsBody):
    SPRITE = "enemy/enemy.png"
    COLUMNS = 10
    FACES_RIGHT = False
    HITBOX = (36, 28)
    SCORE = 1000
    BULLET_SPRITE = "bullet/enemy.png"
    BULLET_SPEED = 320

    PATROL_SPEED_FACTOR = 0.6
    HEARING_RANGE = 70        # detecta al jugador a sus espaldas si está muy cerca
    VERTICAL_TOLERANCE = 40   # solo ve al jugador si está más o menos a su altura
    MEMORY_TIME = 2.0         # segundos que lo sigue buscando después de perderlo
    RESPAWN_DELAY = 1.5
    SHOOTER_DISTANCE = 140    # distancia que mantiene un enemigo que dispara
    FLASH_TIME = 0.12

    def __init__(self, x: float, y: float, *, speed: float = 70, max_health: int = 100,
                 respawns: int = 0, can_shoot: bool = True, contact_damage: int = 25,
                 bullet_damage: int = 15, vision: float = 300,
                 fire_rate: tuple[float, float] = (1.4, 2.4),
                 rng: random.Random | None = None) -> None:
        super().__init__(x, y, *self.HITBOX)
        self.animator = Animator({"walk": load_frames(self.SPRITE, self.COLUMNS)},
                                 frame_time=0.09, faces_right=self.FACES_RIGHT)
        self.rng = rng or random.Random()
        self.spawn_point = (x, y)
        self.speed = speed
        self.max_health = max_health
        self.health = max_health
        self.respawns_left = respawns
        self.can_shoot = can_shoot
        self.contact_damage = contact_damage
        self.bullet_damage = bullet_damage
        self.vision = vision
        self.fire_rate = fire_rate

        self.alive = True
        self.facing = self.rng.choice((-1, 1))
        self.state = State.PATROL
        self._state_timer = 0.0
        self._shoot_timer = self.rng.uniform(*fire_rate)
        self._respawn_timer = 0.0
        self._flash = 0.0
        self._last_seen_x: float | None = None

    # -------------------------------------------------------------- vida
    @property
    def defeated(self) -> bool:
        """Muerto y sin reapariciones pendientes."""
        return not self.alive and self._respawn_timer <= 0 and self.respawns_left == 0

    def take_damage(self, amount: int, source_x: float) -> bool:
        """Devuelve True si el golpe lo mató."""
        if not self.alive:
            return False
        self.health -= amount
        self._flash = self.FLASH_TIME
        # Un disparo por la espalda lo pone en alerta y lo hace darse vuelta.
        self.facing = 1 if source_x > self.rect.centerx else -1
        self._last_seen_x = source_x
        self._set_state(State.SEARCH, self.MEMORY_TIME)
        if self.health > 0:
            return False
        self.alive = False
        if self.respawns_left > 0:
            self.respawns_left -= 1
            self._respawn_timer = self.RESPAWN_DELAY
        return True

    def _respawn(self) -> None:
        self.place(*self.spawn_point)
        self.health = self.max_health
        self.alive = True
        self._set_state(State.PATROL)

    # ------------------------------------------------------------ update
    def update(self, dt: float, solids: Sequence, hazards: Sequence, player) -> list[Bullet]:
        if not self.alive:
            if self._respawn_timer > 0:
                self._respawn_timer -= dt
                if self._respawn_timer <= 0:
                    self._respawn()
            return []

        self._state_timer = max(0.0, self._state_timer - dt)
        self._shoot_timer = max(0.0, self._shoot_timer - dt)
        self._flash = max(0.0, self._flash - dt)

        bullets = self.think(dt, solids, hazards, player)
        self.apply_physics(dt, solids)
        self.animator.update(dt)
        return bullets

    def think(self, dt: float, solids: Sequence, hazards: Sequence, player) -> list[Bullet]:
        if self.can_see(player, solids):
            self._last_seen_x = player.rect.centerx
            self._set_state(State.CHASE)
        elif self.state is State.CHASE:
            self._set_state(State.SEARCH, self.MEMORY_TIME)

        if self.state is State.CHASE:
            return self._chase(player, solids, hazards)
        if self.state is State.SEARCH:
            self._search(solids, hazards)
        elif self.state is State.PAUSE:
            self.velocity.x = 0
            if self._state_timer <= 0:
                self._set_state(State.PATROL)
        else:
            self._patrol(dt, solids, hazards)
        return []

    # ---------------------------------------------------------- estados
    def _patrol(self, dt: float, solids: Sequence, hazards: Sequence) -> None:
        if not self.path_clear(solids, hazards):
            self.facing *= -1
            self.velocity.x = 0
            self._set_state(State.PAUSE, self.rng.uniform(0.2, 0.5))
            return
        if self.rng.random() < dt * 0.15:
            self.velocity.x = 0
            self._set_state(State.PAUSE, self.rng.uniform(0.6, 1.4))
            return
        self.velocity.x = self.facing * self.speed * self.PATROL_SPEED_FACTOR

    def _search(self, solids: Sequence, hazards: Sequence) -> None:
        if self._last_seen_x is None or self._state_timer <= 0:
            self._set_state(State.PATROL)
            return
        dx = self._last_seen_x - self.rect.centerx
        if abs(dx) < 6:
            self.velocity.x = 0
            self._set_state(State.PAUSE, 0.8)
            return
        self.facing = 1 if dx > 0 else -1
        self.velocity.x = self.facing * self.speed if self.path_clear(solids, hazards) else 0

    def _chase(self, player, solids: Sequence, hazards: Sequence) -> list[Bullet]:
        dx = player.rect.centerx - self.rect.centerx
        self.facing = 1 if dx > 0 else -1
        keep_distance = self.SHOOTER_DISTANCE if self.can_shoot else 0
        if abs(dx) > keep_distance and self.path_clear(solids, hazards):
            self.velocity.x = self.facing * self.speed
        else:
            self.velocity.x = 0
        if self.can_shoot and self._shoot_timer <= 0:
            self._shoot_timer = self.rng.uniform(*self.fire_rate)
            return self.shoot(player)
        return []

    def _set_state(self, state: State, duration: float = 0.0) -> None:
        self.state = state
        self._state_timer = duration

    # ---------------------------------------------------------- sentidos
    def can_see(self, player, solids: Iterable) -> bool:
        if not player.alive:
            return False
        dx = player.rect.centerx - self.rect.centerx
        if abs(dx) > self.vision:
            return False
        if abs(player.rect.centery - self.rect.centery) > self.VERTICAL_TOLERANCE + self.rect.height / 2:
            return False
        if dx * self.facing < 0 and abs(dx) > self.HEARING_RANGE:
            return False
        sight_line = (self.rect.center, player.rect.center)
        return not any(solid.rect.clipline(*sight_line) for solid in solids)

    def path_clear(self, solids: Sequence, hazards: Sequence) -> bool:
        """¿Puede seguir caminando hacia donde mira sin chocar, caerse ni pisar una trampa?"""
        if not self.on_ground:
            return True
        if self.blocked_side == self.facing:
            return False
        front_x = self.rect.right + 1 if self.facing > 0 else self.rect.left - 5
        floor_probe = pg.Rect(front_x, self.rect.bottom, 4, 4)
        if not any(floor_probe.colliderect(solid.rect) for solid in solids):
            return False
        body_probe = pg.Rect(front_x, self.rect.top, 4, self.rect.height - 2)
        return not any(body_probe.colliderect(hazard.rect) for hazard in hazards)

    # ----------------------------------------------------------- ataque
    def shoot(self, player) -> list[Bullet]:
        muzzle = (self.rect.centerx + self.facing * self.rect.width / 2, self.rect.centery)
        return [Bullet(muzzle, self.facing, self.bullet_damage, sprite=self.BULLET_SPRITE,
                       speed=self.BULLET_SPEED, lifetime=2.0)]

    # ------------------------------------------------------------- dibujo
    def current_image(self) -> pg.Surface:
        image = self.animator.image(self.facing)
        if self._flash > 0:
            image = image.copy()
            image.fill((110, 110, 110), special_flags=pg.BLEND_RGB_ADD)
        return image

    def draw(self, surface: pg.Surface) -> None:
        if not self.alive:
            return
        image = self.current_image()
        surface.blit(image, image.get_rect(midbottom=self.rect.midbottom))
        if self.health < self.max_health:
            self._draw_health_bar(surface)

    def _draw_health_bar(self, surface: pg.Surface) -> None:
        bar = pg.Rect(0, 0, self.rect.width, 4)
        bar.midbottom = (self.rect.centerx, self.rect.top - 6)
        pg.draw.rect(surface, RED, bar)
        filled = bar.copy()
        filled.width = round(bar.width * self.health / self.max_health)
        pg.draw.rect(surface, GREEN, filled)


class Boss(Enemy):
    """Missigno: siempre sabe dónde está el jugador, salta y entra en furia."""

    SPRITE = "boss/missigno.png"
    COLUMNS = 1
    FACES_RIGHT = True
    HITBOX = (56, 146)
    SCORE = 5000
    SHOOTER_DISTANCE = 200
    JUMP_SPEED = 760
    JUMP_COOLDOWN = 2.5
    GLITCH_COOLDOWN = (5.0, 8.0)
    GLITCH_TIME = 0.4

    def __init__(self, x: float, y: float, *, rng: random.Random | None = None, **kwargs) -> None:
        kwargs = {"speed": 80, "max_health": 400, "contact_damage": 35, "bullet_damage": 20,
                  "vision": WIDTH, "fire_rate": (1.2, 1.8), **kwargs}
        super().__init__(x, y, rng=rng, **kwargs)
        self.name = "MISSIGNO"
        self._base_speed = self.speed
        self._base_fire_rate = self.fire_rate
        self._jump_timer = 0.0
        self._glitch_timer = self.rng.uniform(*self.GLITCH_COOLDOWN)
        self._glitch_fx = 0.0

    @property
    def enraged(self) -> bool:
        return self.health <= self.max_health / 2

    def update(self, dt: float, solids: Sequence, hazards: Sequence, player) -> list[Bullet]:
        self._jump_timer = max(0.0, self._jump_timer - dt)
        self._glitch_fx = max(0.0, self._glitch_fx - dt)
        if self.alive and self.enraged:
            self.speed = self._base_speed * 1.6
            self.fire_rate = (self._base_fire_rate[0] / 2, self._base_fire_rate[1] / 2)
            self._glitch_timer -= dt
            if self._glitch_timer <= 0:
                self._glitch_timer = self.rng.uniform(*self.GLITCH_COOLDOWN)
                self.glitch_teleport(solids, player)
        return super().update(dt, solids, hazards, player)

    def can_see(self, player, solids: Iterable) -> bool:
        # El jefe no necesita línea de visión: siente al jugador en todo el nivel.
        return player.alive

    def path_clear(self, solids: Sequence, hazards: Sequence) -> bool:
        # Puede pisar trampas; solo lo frenan las paredes y los bordes.
        return super().path_clear(solids, ())

    def _chase(self, player, solids: Sequence, hazards: Sequence) -> list[Bullet]:
        player_above = player.rect.bottom < self.rect.bottom - 60
        close = abs(player.rect.centerx - self.rect.centerx) < 220
        if player_above and close and self.on_ground and self._jump_timer <= 0:
            self.velocity.y = -self.JUMP_SPEED
            self._jump_timer = self.JUMP_COOLDOWN
        return super()._chase(player, solids, hazards)

    def shoot(self, player) -> list[Bullet]:
        # Apunta a la altura del jugador dentro de lo que le permite su cuerpo.
        low, high = self.rect.top + 12, self.rect.bottom - 12
        aim_y = max(low, min(player.rect.centery, high))
        heights = [aim_y]
        if self.enraged:
            # Abanico de 3 balas: la apuntada y las dos alturas más cercanas
            # que todavía salen de su cuerpo.
            spread = [aim_y + step * 45 for step in (-2, -1, 1, 2)]
            heights += sorted((y for y in spread if low <= y <= high),
                              key=lambda y: abs(y - aim_y))[:2]
        muzzle_x = self.rect.centerx + self.facing * self.rect.width / 2
        return [
            Bullet((muzzle_x, y), self.facing, self.bullet_damage, sprite=self.BULLET_SPRITE,
                   speed=self.BULLET_SPEED + 60, lifetime=2.5)
            for y in heights
        ]

    def glitch_teleport(self, solids: Sequence, player) -> bool:
        """Reaparece sobre otra plataforma libre, lejos del jugador."""
        tops = [s.rect for s in solids if s.rect.width >= self.rect.width]
        for _ in range(20):
            platform = self.rng.choice(tops)
            x = self.rng.randint(platform.left, platform.right - self.rect.width)
            candidate = pg.Rect(x, platform.top - self.rect.height, *self.rect.size)
            if candidate.top < 0 or candidate.bottom > HEIGHT:
                continue
            if any(candidate.colliderect(s.rect) for s in solids):
                continue
            if abs(candidate.centerx - player.rect.centerx) < 120:
                continue
            self.place(*candidate.topleft)
            self._glitch_fx = self.GLITCH_TIME
            return True
        return False

    def draw(self, surface: pg.Surface) -> None:
        if not self.alive:
            return
        image = self.current_image()
        target = image.get_rect(midbottom=self.rect.midbottom)
        if self._glitch_fx > 0 or (self.enraged and random.random() < 0.04):
            # Efecto de aberración cromática: copias corridas en rojo y cian.
            for color, offset in (((255, 0, 0), -5), ((0, 255, 255), 5)):
                ghost = image.copy()
                ghost.fill(color, special_flags=pg.BLEND_RGB_MULT)
                ghost.set_alpha(140)
                surface.blit(ghost, target.move(offset, random.randint(-3, 3)))
        surface.blit(image, target)
