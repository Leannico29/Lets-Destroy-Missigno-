"""Tabla de puntajes persistida en CSV (se guarda el mejor puntaje de cada jugador)."""
from __future__ import annotations

import csv
from pathlib import Path

from game.settings import SCORES_FILE

HEADER = ["Nombre", "Puntaje"]


def load_scores(path: Path = SCORES_FILE) -> dict[str, int]:
    if not path.exists():
        return {}
    scores: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)  # encabezado
        for row in reader:
            if len(row) < 2 or not row[0].strip():
                continue
            try:
                points = int(row[1])
            except ValueError:
                continue
            name = row[0].strip()
            scores[name] = max(points, scores.get(name, points))
    return scores


def save_score(name: str, points: int, path: Path = SCORES_FILE) -> None:
    scores = load_scores(path)
    scores[name] = max(points, scores.get(name, points))
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(HEADER)
        writer.writerows(_sorted(scores))


def top_scores(limit: int = 3, path: Path = SCORES_FILE) -> list[tuple[str, int]]:
    return _sorted(load_scores(path))[:limit]


def _sorted(scores: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
