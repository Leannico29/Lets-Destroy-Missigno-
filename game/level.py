"""Bucle de juego de un nivel: entrada, simulación, colisiones y dibujo."""
from __future__ import annotations

import random
from enum import Enum, auto

import pygame as pg

from game.assets import Audio, load_image
from game.entities import Boss, Bullet, Enemy, Fruit, Platform, Player, Trap
from game.entities.player import JUMP_KEYS, SHOOT_KEYS
from game.levels import LevelData
from game.settings import FPS, GREEN, HEIGHT, MAX_FRAME_TIME, ORANGE, RED, WHITE, WIDTH, YELLOW
from game.ui import Fonts, draw_bar, draw_overlay, draw_text, health_color

SHOOT_SOUND = "sonido disparo.mp3"
DAMAGE_PENALTY = 25
TIME_BONUS_PER_SECOND = 10
END_BANNER_TIME = 2.0


class Outcome(Enum):
    CLEARED = auto()
    FAILED = auto()
    QUIT = auto()


class Phase(Enum):
    PLAYING = auto()
    PAUSED = auto()
    CLEARED = auto()
    DYING = auto()


class Level:
    def __init__(self, data: LevelData, screen: pg.Surface, clock: pg.time.Clock,
                 audio: Audio, fonts: Fonts, score: int = 0,
                 rng: random.Random | None = None) -> None:
        self.data = data
        self.screen = screen
        self.clock = clock
        self.audio = audio
        self.fonts = fonts
        self.score = score
        self.rng = rng or random.Random()
        self.debug = False

        self.background = load_image(data.background, (WIDTH, HEIGHT))
        self.platforms = [Platform(*rect) for rect in data.platforms]
        self.traps = pg.sprite.Group(Trap(x, y) for x, y in data.traps)
        self.fruits = pg.sprite.Group(Fruit(f.x, f.y, f.kind) for f in data.fruits)
        self.player = Player(*data.player_start, max_health=data.player_health)
        self.enemies: list[Enemy] = [self._create_enemy(spawn) for spawn in data.enemies]
        self.player_bullets: pg.sprite.Group = pg.sprite.Group()
        self.enemy_bullets: pg.sprite.Group = pg.sprite.Group()

        self.phase = Phase.PLAYING
        self.time_left = float(data.time_limit)
        self._banner_timer = 0.0
        self.time_bonus = 0

    def _create_enemy(self, spawn) -> Enemy:
        if spawn.boss:
            return Boss(spawn.x, spawn.y, rng=self.rng)
        return Enemy(spawn.x, spawn.y, speed=spawn.speed, max_health=spawn.max_health,
                     respawns=spawn.respawns, can_shoot=spawn.can_shoot, rng=self.rng)

    @property
    def boss(self) -> Boss | None:
        return next((e for e in self.enemies if isinstance(e, Boss)), None)

    # ------------------------------------------------------------- bucle
    def run(self) -> Outcome:
        self.audio.play_music(self.data.music)
        while True:
            dt = min(self.clock.tick(FPS) / 1000, MAX_FRAME_TIME)
            outcome = self.handle_events()
            if outcome is None:
                outcome = self.update(dt)
            self.draw()
            pg.display.flip()
            if outcome is not None:
                return outcome

    def handle_events(self) -> Outcome | None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return Outcome.QUIT
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_ESCAPE, pg.K_p) and self.phase in (Phase.PLAYING, Phase.PAUSED):
                    self.phase = Phase.PAUSED if self.phase is Phase.PLAYING else Phase.PLAYING
                elif event.key == pg.K_m:
                    self.audio.toggle_mute()
                elif event.key == pg.K_F1:
                    self.debug = not self.debug
                elif event.key in JUMP_KEYS and self.phase is Phase.PLAYING:
                    self.player.request_jump()
            elif event.type == pg.KEYUP and event.key in JUMP_KEYS:
                self.player.release_jump()
        return None

    def update(self, dt: float) -> Outcome | None:
        if self.phase is Phase.PAUSED:
            return None

        if self.phase is Phase.PLAYING:
            keys = pg.key.get_pressed()
            self.player.handle_input(keys)
            if any(keys[k] for k in SHOOT_KEYS):
                self._add_bullet(self.player.try_shoot(), self.player_bullets)
            self.time_left = max(0.0, self.time_left - dt)
            if self.time_left == 0:
                self.player.die()

        self.player.update(dt, self.platforms)
        hazards = self.traps.sprites()
        for enemy in self.enemies:
            for bullet in enemy.update(dt, self.platforms, hazards, self.player):
                self._add_bullet(bullet, self.enemy_bullets)
        self.player_bullets.update(dt, self.platforms)
        self.enemy_bullets.update(dt, self.platforms)
        self.fruits.update(dt)

        if self.phase is Phase.PLAYING:
            self._resolve_combat()
            self._collect_fruits()
            self._check_end_conditions()
        return self._advance_end_phase(dt)

    # --------------------------------------------------------- reglas
    def _add_bullet(self, bullet: Bullet | None, group: pg.sprite.Group) -> None:
        if bullet is not None:
            group.add(bullet)
            self.audio.play_sound(SHOOT_SOUND)

    def _hurt_player(self, amount: int) -> None:
        if self.player.take_damage(amount):
            self.score = max(0, self.score - DAMAGE_PENALTY)

    def _resolve_combat(self) -> None:
        living = [e for e in self.enemies if e.alive]
        for bullet in list(self.player_bullets):
            target = next((e for e in living if e.alive and bullet.rect.colliderect(e.rect)), None)
            if target is not None:
                bullet.kill()
                if target.take_damage(bullet.damage, self.player.rect.centerx):
                    self.score += target.SCORE

        for bullet in list(self.enemy_bullets):
            if bullet.rect.colliderect(self.player.rect):
                bullet.kill()
                self._hurt_player(bullet.damage)

        for enemy in living:
            if enemy.alive and enemy.rect.colliderect(self.player.rect):
                self._hurt_player(enemy.contact_damage)

        if any(trap.hitbox.colliderect(self.player.rect) for trap in self.traps):
            self._hurt_player(Trap.DAMAGE)

    def _collect_fruits(self) -> None:
        for fruit in pg.sprite.spritecollide(self.player, self.fruits, dokill=True):
            self.player.heal()
            self.score += Fruit.SCORE

    def _check_end_conditions(self) -> None:
        if not self.player.alive:
            self.phase = Phase.DYING
            self._banner_timer = END_BANNER_TIME
        elif not self.fruits and all(e.defeated for e in self.enemies):
            self.phase = Phase.CLEARED
            self._banner_timer = END_BANNER_TIME
            self.time_bonus = int(self.time_left) * TIME_BONUS_PER_SECOND
            self.score += self.time_bonus
            self.player.velocity.x = 0

    def _advance_end_phase(self, dt: float) -> Outcome | None:
        if self.phase is Phase.CLEARED:
            self._banner_timer -= dt
            return Outcome.CLEARED if self._banner_timer <= 0 else None
        if self.phase is Phase.DYING and self.player.death_animation_done:
            self._banner_timer -= dt
            return Outcome.FAILED if self._banner_timer <= 0 else None
        return None

    # ---------------------------------------------------------- dibujo
    def draw(self) -> None:
        screen = self.screen
        screen.blit(self.background, (0, 0))
        for platform in self.platforms:
            screen.blit(platform.image, platform.rect)
        self.traps.draw(screen)
        self.fruits.draw(screen)
        for enemy in self.enemies:
            enemy.draw(screen)
        self.player.draw(screen)
        self.player_bullets.draw(screen)
        self.enemy_bullets.draw(screen)
        if self.debug:
            self._draw_debug()
        self._draw_hud()
        self._draw_phase_overlay()

    def _draw_hud(self) -> None:
        fonts, screen = self.fonts, self.screen
        draw_text(screen, fonts.normal, f"{self.score:06d}", ORANGE, topleft=(12, 10))
        draw_text(screen, fonts.small, self.data.name, WHITE, topleft=(12, 40))

        seconds = int(self.time_left)
        timer_color = GREEN if seconds > 30 else YELLOW if seconds > 10 else RED
        draw_text(screen, fonts.normal, f"{seconds // 60:02d}:{seconds % 60:02d}", timer_color,
                  midtop=(WIDTH // 2, 10))

        ratio = self.player.health / self.player.max_health
        bar = pg.Rect(WIDTH - 172, 14, 160, 16)
        draw_bar(screen, bar, ratio, health_color(ratio))
        draw_text(screen, fonts.small, f"Vida {self.player.health}/{self.player.max_health}",
                  WHITE, midtop=(bar.centerx, bar.bottom + 4))

        boss = self.boss
        if boss is not None and boss.alive:
            boss_bar = pg.Rect(WIDTH // 2 - 150, HEIGHT - 28, 300, 12)
            draw_bar(screen, boss_bar, boss.health / boss.max_health, RED)
            label = f"{boss.name}  ¡FURIA!" if boss.enraged else boss.name
            draw_text(screen, fonts.small, label, WHITE, midbottom=(boss_bar.centerx, boss_bar.top - 4))

    def _draw_phase_overlay(self) -> None:
        fonts, screen = self.fonts, self.screen
        center = (WIDTH // 2, HEIGHT // 2)
        if self.phase is Phase.PAUSED:
            draw_overlay(screen)
            draw_text(screen, fonts.large, "Pausa", WHITE, center=center)
            draw_text(screen, fonts.small, "Esc o P para seguir  ·  M silencia el sonido", WHITE,
                      center=(center[0], center[1] + 45))
        elif self.phase is Phase.CLEARED:
            draw_overlay(screen)
            draw_text(screen, fonts.large, "¡Nivel superado!", GREEN, center=center)
            draw_text(screen, fonts.normal, f"Bonus de tiempo: +{self.time_bonus}", ORANGE,
                      center=(center[0], center[1] + 50))
        elif self.phase is Phase.DYING and self.player.death_animation_done:
            draw_overlay(screen)
            message = "Se acabó el tiempo" if self.time_left == 0 else "Game over"
            draw_text(screen, fonts.large, message, RED, center=center)

    def _draw_debug(self) -> None:
        for platform in self.platforms:
            pg.draw.rect(self.screen, (0, 160, 255), platform.rect, 1)
        for trap in self.traps:
            pg.draw.rect(self.screen, (255, 0, 255), trap.hitbox, 1)
        pg.draw.rect(self.screen, GREEN, self.player.rect, 1)
        for enemy in self.enemies:
            if enemy.alive:
                pg.draw.rect(self.screen, RED, enemy.rect, 1)
                draw_text(self.screen, self.fonts.small, enemy.state.name, WHITE,
                          midbottom=(enemy.rect.centerx, enemy.rect.top - 12))
        draw_text(self.screen, self.fonts.small, f"{self.clock.get_fps():.0f} FPS", WHITE,
                  bottomleft=(10, HEIGHT - 8))
