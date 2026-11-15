"""Punto de entrada: `python main.py`."""
import logging

from game.app import Game


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    Game().run()


if __name__ == "__main__":
    main()
