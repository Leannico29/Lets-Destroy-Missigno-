import unittest
from types import SimpleNamespace

import pygame as pg

from game.entities.physics import PhysicsBody

DT = 1 / 60


def solid(x, y, w, h):
    return SimpleNamespace(rect=pg.Rect(x, y, w, h))


GROUND = solid(0, 500, 800, 100)


def simulate(body, solids, seconds):
    for _ in range(round(seconds / DT)):
        body.apply_physics(DT, solids)


class PhysicsBodyTest(unittest.TestCase):
    def test_lands_and_stays_on_ground(self):
        body = PhysicsBody(100, 300, 20, 30)
        simulate(body, [GROUND], 1.0)
        self.assertEqual(body.rect.bottom, GROUND.rect.top)
        for _ in range(120):  # sin parpadeo de on_ground mientras está quieto
            body.apply_physics(DT, [GROUND])
            self.assertTrue(body.on_ground)

    def test_wall_stops_horizontal_movement(self):
        """Regresión del bug de paredes: el cuerpo no atraviesa ni sube el bloque."""
        wall = solid(300, 400, 75, 100)
        body = PhysicsBody(200, 470, 20, 30)
        body.velocity.x = 270
        for _ in range(120):
            body.velocity.x = 270
            body.apply_physics(DT, [GROUND, wall])
        self.assertEqual(body.rect.right, wall.rect.left)
        self.assertEqual(body.rect.bottom, GROUND.rect.top)
        self.assertEqual(body.blocked_side, 1)

    def test_ceiling_cuts_jump_without_teleporting_on_top(self):
        ceiling = solid(50, 400, 200, 40)
        body = PhysicsBody(100, 470, 20, 30)
        body.velocity.y = -700
        simulate(body, [GROUND, ceiling], 0.2)
        self.assertGreaterEqual(body.rect.top, ceiling.rect.bottom)
        simulate(body, [GROUND, ceiling], 1.0)
        self.assertEqual(body.rect.bottom, GROUND.rect.top)

    def test_screen_edges_are_walls(self):
        body = PhysicsBody(10, 470, 20, 30)
        for _ in range(60):
            body.velocity.x = -300
            body.apply_physics(DT, [GROUND])
        self.assertEqual(body.rect.left, 0)


if __name__ == "__main__":
    unittest.main()
