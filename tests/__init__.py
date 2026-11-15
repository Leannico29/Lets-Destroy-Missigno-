import os

# Permite correr los tests sin ventana ni placa de sonido (por ejemplo en CI).
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
