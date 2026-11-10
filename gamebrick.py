import tkinter as tk
import random
import math
import json
import threading
from pathlib import Path

try:
    import winsound  
except ImportError:
    winsound = None


WIDTH = 900
HEIGHT = 650
FPS = 16

# Ukuran balok
BLOCK_W = 54
BLOCK_H = 18
BLOCK_GAP_X = 10
BLOCK_GAP_Y = 10
BLOCK_COLUMNS = 12

# Tinggi panel HUD
HUD_H = 46

# Warna dasar
BG = "#d4e6ff"         
GRID = "#c2daf8"        
PANEL = "#ffffff"
TEXT = "#4a4768"        
ACCENT = "#8fa8d9"      

# 5 warna pastel untuk balok
PINK = "#ffb3c6"
PEACH = "#ffd6a5"
MINT = "#b5ead7"
SKY = "#a0c4ff"
LAVENDER = "#cdb4db"
BLOCK_COLORS = [PINK, PEACH, MINT, SKY, LAVENDER]

# Warna balok yang sudah kena sekali (balok kuat)
CRACKED = "#fff3b0"

# Warna striker & bola
STRIKER_COLOR = "#ffd6a5"
BALL_COLOR = "#ff8fab"

# Warna teks aksen
GOLD = "#b8901a"
BLUE_TEXT = "#3f78b0"
PINK_TEXT = "#e0608a"
GREEN_TEXT = "#3fa380"
RED_TEXT = "#e5707e"

HIGH_SCORE_FILE = Path("pastel_highscore.json")

# Nada suara: (frekuensi Hz, durasi ms)
SOUNDS = {
    "start": [(523, 100), (659, 100), (784, 160)],
    "level_clear": [(784, 100), (988, 100), (1175, 100), (1568, 280)],
    "game_over": [(494, 220), (392, 220), (330, 220), (262, 550)],
}


def _play_notes(notes):
    for freq, duration in notes:
        try:
            winsound.Beep(freq, duration)
        except RuntimeError:
            pass


def load_high_score():
    try:
        data = json.loads(
            HIGH_SCORE_FILE.read_text(encoding="utf-8")
        )
        return int(data.get("high_score", 0))
    except (OSError, ValueError, TypeError):
        return 0


def save_high_score(score):
    try:
        HIGH_SCORE_FILE.write_text(
            json.dumps({"high_score": score}, indent=4),
            encoding="utf-8"
        )
    except OSError:
        pass