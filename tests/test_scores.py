import tempfile
import unittest
from pathlib import Path

from game.scores import load_scores, save_score, top_scores


class ScoresTest(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = Path(self._dir.name) / "scores.csv"

    def tearDown(self):
        self._dir.cleanup()

    def test_missing_file_means_no_scores(self):
        self.assertEqual(load_scores(self.path), {})

    def test_keeps_best_score_per_player(self):
        save_score("lean", 2900, self.path)
        save_score("lean", 500, self.path)
        save_score("lean", 6000, self.path)
        self.assertEqual(load_scores(self.path), {"lean": 6000})

    def test_top_scores_are_sorted_and_limited(self):
        for name, points in [("a", 10), ("b", 300), ("c", 50), ("d", 200)]:
            save_score(name, points, self.path)
        self.assertEqual(top_scores(3, self.path), [("b", 300), ("d", 200), ("c", 50)])

    def test_ignores_corrupt_rows(self):
        self.path.write_text("Nombre,Puntaje\nlean, 2900\nroto\nx,abc\n", encoding="utf-8")
        self.assertEqual(load_scores(self.path), {"lean": 2900})


if __name__ == "__main__":
    unittest.main()
