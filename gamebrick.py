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


class Striker:
    def __init__(self, canvas):
        self.canvas = canvas
        self.width = 110
        self.height = 14
        self.speed = 9
        self.x = WIDTH // 2
        self.y = HEIGHT - 90

        self.id = canvas.create_rectangle(
            self.x - self.width // 2,
            self.y,
            self.x + self.width // 2,
            self.y + self.height,
            fill=STRIKER_COLOR,
            outline=TEXT,
            width=2
        )

    def update(self, direction):
        self.x += direction * self.speed
        self.x = max(
            self.width // 2 + 12,
            min(WIDTH - self.width // 2 - 12, self.x)
        )

        self.canvas.coords(
            self.id,
            self.x - self.width // 2,
            self.y,
            self.x + self.width // 2,
            self.y + self.height
        )

    def get_rect(self):
        return (
            self.x - self.width // 2,
            self.y,
            self.x + self.width // 2,
            self.y + self.height
        )


class Ball:
    def __init__(self, canvas, level=1):
        self.canvas = canvas
        self.radius = 8
        self.speed = 5.2 + min(level - 1, 8) * 0.35

        self.x = WIDTH / 2
        self.y = HEIGHT - 112

        self.dx = random.choice([-0.65, 0.65])
        self.dy = -0.76

        self.normalize()

        self.id = canvas.create_oval(
            self.x - self.radius,
            self.y - self.radius,
            self.x + self.radius,
            self.y + self.radius,
            fill=BALL_COLOR,
            outline=TEXT,
            width=2
        )

    def normalize(self):
        length = math.sqrt(self.dx ** 2 + self.dy ** 2)

        if length:
            self.dx /= length
            self.dy /= length

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

        if self.x - self.radius <= 12:
            self.x = 12 + self.radius
            self.dx = abs(self.dx)

        elif self.x + self.radius >= WIDTH - 12:
            self.x = WIDTH - 12 - self.radius
            self.dx = -abs(self.dx)

        top_wall = HUD_H + 8
        if self.y - self.radius <= top_wall:
            self.y = top_wall + self.radius
            self.dy = abs(self.dy)

        self.canvas.coords(
            self.id,
            self.x - self.radius,
            self.y - self.radius,
            self.x + self.radius,
            self.y + self.radius
        )

        return self.y - self.radius > HEIGHT - 65

    def bounce_paddle(self, paddle):
        offset = (
            self.x - paddle.x
        ) / (paddle.width / 2)

        self.dx = max(-0.9, min(0.9, offset))
        self.dy = -math.sqrt(max(0.1, 1 - self.dx ** 2))
        self.normalize()

    def bounce_block(self, block):
        x1, y1, x2, y2 = block.get_rect()

        overlap_x = min(
            self.x + self.radius - x1,
            x2 - (self.x - self.radius)
        )

        overlap_y = min(
            self.y + self.radius - y1,
            y2 - (self.y - self.radius)
        )

        if overlap_x < overlap_y:
            self.dx *= -1
        else:
            self.dy *= -1


class Block:
    COLORS = BLOCK_COLORS

    def __init__(self, canvas, x, y, level):
        self.canvas = canvas
        self.width = BLOCK_W
        self.height = BLOCK_H

        self.x = x
        self.y = y

        self.color = random.choice(self.COLORS)

        self.health = (
            1 if level == 1 else random.choice([1, 1, 2])
        )

        self.id = canvas.create_rectangle(
            x, y,
            x + self.width,
            y + self.height,
            fill=self.color,
            outline=TEXT,
            width=1
        )

    def hit(self):
        self.health -= 1

        if self.health <= 0:
            self.canvas.delete(self.id)
            return True

        self.canvas.itemconfigure(
            self.id,
            fill=CRACKED
        )
        return False

    def get_rect(self):
        return (
            self.x,
            self.y,
            self.x + self.width,
            self.y + self.height
        )


class Particle:
    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.color = color

        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.2, 4.2)

        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed

        self.life = random.randint(18, 32)
        self.size = random.randint(2, 4)

        self.id = canvas.create_oval(
            x, y,
            x + self.size,
            y + self.size,
            fill=color,
            outline=""
        )

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += 0.06
        self.life -= 1

        self.canvas.coords(
            self.id,
            self.x,
            self.y,
            self.x + self.size,
            self.y + self.size
        )

        if self.life <= 0:
            self.canvas.delete(self.id)
            return False

        return True
