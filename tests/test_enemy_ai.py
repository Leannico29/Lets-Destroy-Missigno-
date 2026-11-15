import random
import unittest
from types import SimpleNamespace

import pygame as pg

from game.entities.enemy import Boss, Enemy, State
from game.entities.player import Player

DT = 1 / 60


def solid(x, y, w, h):
    return SimpleNamespace(rect=pg.Rect(x, y, w, h))


GROUND = solid(0, 530, 800, 70)
LEDGE = solid(200, 300, 300, 30)
FAR_AWAY = (700, 490)


def run(enemy, solids, player, seconds, hazards=()):
    bullets = []
    for _ in range(round(seconds / DT)):
        bullets += enemy.update(DT, solids, list(hazards), player)
    return bullets


class EnemyAITest(unittest.TestCase):
    def make_enemy(self, x, y, **kwargs):
        return Enemy(x, y, rng=random.Random(1), **kwargs)

    def test_patrol_never_walks_off_its_platform(self):
        enemy = self.make_enemy(330, 260)
        player = Player(*FAR_AWAY)
        for _ in range(20 * 60):
            enemy.update(DT, [GROUND, LEDGE], [], player)
            if enemy.on_ground:
                self.assertEqual(enemy.rect.bottom, LEDGE.rect.top)
                self.assertGreaterEqual(enemy.rect.left, LEDGE.rect.left - 1)
                self.assertLessEqual(enemy.rect.right, LEDGE.rect.right + 1)

    def test_patrol_turns_around_before_traps(self):
        trap = SimpleNamespace(rect=pg.Rect(420, 500, 30, 30))
        enemy = self.make_enemy(300, 500)
        player = Player(20, 100)
        for _ in range(20 * 60):
            enemy.update(DT, [GROUND], [trap], player)
            self.assertFalse(enemy.rect.colliderect(trap.rect))

    def test_chases_and_shoots_player_on_same_level(self):
        enemy = self.make_enemy(400, 500, fire_rate=(0.5, 0.5))
        enemy.facing = -1
        player = Player(250, 500)
        bullets = run(enemy, [GROUND], player, 1.5)
        self.assertIs(enemy.state, State.CHASE)
        self.assertTrue(bullets)
        self.assertTrue(all(b.direction == -1 for b in bullets))

    def test_walls_block_line_of_sight(self):
        wall = solid(320, 380, 40, 150)
        enemy = self.make_enemy(400, 500)
        enemy.facing = -1
        player = Player(250, 500)
        self.assertFalse(enemy.can_see(player, [GROUND, wall]))
        self.assertTrue(enemy.can_see(player, [GROUND]))

    def test_shot_in_the_back_makes_it_turn_and_search(self):
        enemy = self.make_enemy(400, 500)
        enemy.facing = 1
        enemy.take_damage(10, source_x=100)
        self.assertEqual(enemy.facing, -1)
        self.assertIs(enemy.state, State.SEARCH)

    def test_respawns_once_before_being_defeated(self):
        enemy = self.make_enemy(400, 500, respawns=1)
        player = Player(*FAR_AWAY)
        self.assertTrue(enemy.take_damage(999, 0))
        self.assertFalse(enemy.defeated)
        run(enemy, [GROUND], player, enemy.RESPAWN_DELAY + 0.1)
        self.assertTrue(enemy.alive)
        enemy.take_damage(999, 0)
        self.assertTrue(enemy.defeated)


class BossTest(unittest.TestCase):
    def test_enrages_at_half_health_and_fires_spread(self):
        boss = Boss(300, 300, rng=random.Random(2))
        player = Player(100, 500)
        run(boss, [GROUND], player, 0.5)
        boss.take_damage(boss.max_health // 2, source_x=100)
        self.assertTrue(boss.enraged)
        self.assertEqual(len(boss.shoot(player)), 3)

    def test_glitch_teleport_lands_on_free_spot_away_from_player(self):
        block = solid(500, 380, 75, 150)
        boss = Boss(100, 300, rng=random.Random(3))
        player = Player(120, 500)
        self.assertTrue(boss.glitch_teleport([GROUND, block], player))
        self.assertFalse(boss.rect.colliderect(block.rect))
        self.assertGreaterEqual(abs(boss.rect.centerx - player.rect.centerx), 120)


if __name__ == "__main__":
    unittest.main()
