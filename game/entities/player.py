"""Personaje controlado por el jugador."""
from __future__ import annotations

from typing import Iterable

import pygame as pg

from game.assets import load_frames
from game.entities.animation import Animator
from game.entities.bullet import Bullet
from game.entities.physics import PhysicsBody

LEFT_KEYS = (pg.K_LEFT, pg.K_a)
RIGHT_KEYS = (pg.K_RIGHT, pg.K_d)
RUN_KEYS = (pg.K_LSHIFT, pg.K_RSHIFT)
SHOOT_KEYS = (pg.K_q, pg.K_j)
JUMP_KEYS = (pg.K_SPACE, pg.K_UP, pg.K_w)


class Player(PhysicsBody):
    WALK_SPEED = 170
    RUN_SPEED = 270
    JUMP_SPEED = 700          # alcanza ~135 px de altura con la gravedad actual
    JUMP_CUT = 0.45           # soltar el salto antes de tiempo lo acorta
    COYOTE_TIME = 0.10        # margen para saltar justo después de dejar el borde
    JUMP_BUFFER = 0.12        # margen para apretar salto un instante antes de aterrizar
    SHOOT_COOLDOWN = 0.35
    INVULNERABLE_TIME = 1.0
    STUN_TIME = 0.25
    BULLET_DAMAGE = 50

    def __init__(self, x: float, y: float, max_health: int = 100) -> None:
        # El sprite mide 32x32 pero tiene aire a los costados: la hitbox es
        # más angosta para que las paredes se sientan justas.
        super().__init__(x, y, 22, 30)
        self.animator = Animator({
            "idle": load_frames("player/idle.png", 11),
            "walk": load_frames("player/walk.png", 12),
            "run": load_frames("player/run.png", 6),
            "jump": load_frames("player/jump.png", 1),
            "fall": load_frames("player/fall.png", 1),
            "hit": load_frames("player/hit.png", 7),
            "disappear": load_frames("player/disappear.png", 7),
        }, frame_time=0.06)
        self.max_health = max_health
        self.health = max_health
        self.facing = 1
        self.alive = True
        self._running = False
        self._coyote = 0.0
        self._jump_buffer = 0.0
        self._shoot_timer = 0.0
        self._invulnerable = 0.0
        self._stun = 0.0
        self._clock = 0.0

    # ----------------------------------------------------------------- input
    def handle_input(self, keys: pg.key.ScancodeWrapper) -> None:
        if not self.alive:
            return
        direction = int(any(keys[k] for k in RIGHT_KEYS)) - int(any(keys[k] for k in LEFT_KEYS))
        if self._stun > 0:
            direction = 0
        self._running = direction != 0 and any(keys[k] for k in RUN_KEYS)
        self.velocity.x = direction * (self.RUN_SPEED if self._running else self.WALK_SPEED)
        if direction:
            self.facing = direction

    def request_jump(self) -> None:
        if self.alive:
            self._jump_buffer = self.JUMP_BUFFER

    def release_jump(self) -> None:
        if self.velocity.y < 0:
            self.velocity.y *= self.JUMP_CUT

    def try_shoot(self) -> Bullet | None:
        if not self.alive or self._shoot_timer > 0:
            return None
        self._shoot_timer = self.SHOOT_COOLDOWN
        muzzle = (self.rect.centerx + self.facing * 14, self.rect.centery - 2)
        return Bullet(muzzle, self.facing, self.BULLET_DAMAGE, sprite="bullet/player.png")

    # ----------------------------------------------------------------- salud
    @property
    def invulnerable(self) -> bool:
        return self._invulnerable > 0

    def take_damage(self, amount: int) -> bool:
        """Aplica daño si no está en su ventana de invulnerabilidad."""
        if not self.alive or self.invulnerable:
            return False
        self.health = max(0, self.health - amount)
        if self.health == 0:
            self.die()
        else:
            self._invulnerable = self.INVULNERABLE_TIME
            self._stun = self.STUN_TIME
        return True

    def heal(self) -> None:
        self.health = self.max_health

    def die(self) -> None:
        if self.alive:
            self.alive = False
            self.health = 0
            self.velocity.x = 0
            self.animator.play("disappear", loop=False)

    @property
    def death_animation_done(self) -> bool:
        return not self.alive and self.animator.finished

    # ---------------------------------------------------------------- update
    def update(self, dt: float, solids: Iterable) -> None:
        self._clock += dt
        for timer in ("_shoot_timer", "_invulnerable", "_stun", "_jump_buffer"):
            setattr(self, timer, max(0.0, getattr(self, timer) - dt))

        if self.alive:
            self._coyote = self.COYOTE_TIME if self.on_ground else max(0.0, self._coyote - dt)
            if self._jump_buffer > 0 and self._coyote > 0:
                self.velocity.y = -self.JUMP_SPEED
                self._jump_buffer = 0.0
                self._coyote = 0.0
            self.apply_physics(dt, solids)
        self._choose_animation()
        self.animator.update(dt)

    def _choose_animation(self) -> None:
        if not self.alive:
            return
        if self._stun > 0:
            self.animator.play("hit")
        elif not self.on_ground:
            self.animator.play("jump" if self.velocity.y < 0 else "fall")
        elif self.velocity.x:
            self.animator.play("run" if self._running else "walk")
        else:
            self.animator.play("idle")

    def draw(self, surface: pg.Surface) -> None:
        # Parpadeo mientras es invulnerable.
        if self.alive and self.invulnerable and int(self._clock * 16) % 2:
            return
        image = self.animator.image(self.facing)
        if self.alive:
            target = image.get_rect(midbottom=self.rect.midbottom)
        else:  # la animación de desaparición es más grande (96x96)
            target = image.get_rect(center=self.rect.center)
        surface.blit(image, target)
