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

# Kecepatan bola (dulu 5.2 dan 0.35)
BALL_SPEED = 7.5
BALL_SPEED_PER_LEVEL = 0.8

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
        self.speed = BALL_SPEED + min(level - 1, 8) * BALL_SPEED_PER_LEVEL

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


class BrickBreaker:

    def __init__(self, root):
        self.root = root
        self.root.title("BRICK BREAKER")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=WIDTH,
            height=HEIGHT,
            bg=BG,
            highlightthickness=0
        )
        self.canvas.pack()

        self.keys = set()
        self.high_score = load_high_score()

        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.root.bind("<Left>", self.key_down)
        self.root.bind("<Right>", self.key_down)

        self.state = "menu"
        self.reset_game()
        self.state = "menu"

        self.draw_menu()

    # Memainkan suara. Di Windows memakai winsound (di thread
    # terpisah supaya game tidak berhenti), di sistem lain
    # memakai bunyi bell bawaan tkinter
    def play_sound(self, name):
        if winsound is not None:
            threading.Thread(
                target=_play_notes,
                args=(SOUNDS[name],),
                daemon=True
            ).start()
        else:
            self.root.bell()

    def reset_game(self):
        self.canvas.delete("all")

        self.score = 0
        self.level = 1
        self.combo = 0
        self.combo_timer = 0
        self.particles = []

        self.draw_background()
        self.draw_hud()

        self.paddle = Striker(self.canvas)
        self.ball = Ball(self.canvas, self.level)
        self.blocks = self.create_blocks()

        self.update_hud()

    def draw_background(self):
        for x in range(0, WIDTH, 45):
            self.canvas.create_line(
                x, 0, x, HEIGHT,
                fill=GRID
            )

        for y in range(0, HEIGHT, 45):
            self.canvas.create_line(
                0, y, WIDTH, y,
                fill=GRID
            )

    def draw_hud(self):
        self.canvas.create_rectangle(
            0, 0, WIDTH, HUD_H,
            fill=PANEL,
            outline=ACCENT,
            width=2
        )

        mid = HUD_H // 2

        self.score_text = self.canvas.create_text(
            130, mid,
            text="SCORE 0",
            fill=TEXT,
            font=("Consolas", 12, "bold")
        )

        self.best_text = self.canvas.create_text(
            350, mid,
            text="BEST 0",
            fill=GOLD,
            font=("Consolas", 11)
        )

        self.level_text = self.canvas.create_text(
            570, mid,
            text="LEVEL 1",
            fill=BLUE_TEXT,
            font=("Consolas", 11)
        )

        self.combo_text = self.canvas.create_text(
            770, mid,
            text="COMBO x0",
            fill=PINK_TEXT,
            font=("Consolas", 11)
        )

    def update_hud(self):
        self.canvas.itemconfigure(
            self.score_text,
            text=f"SCORE {self.score}"
        )

        self.canvas.itemconfigure(
            self.best_text,
            text=f"BEST {max(self.high_score, self.score)}"
        )

        self.canvas.itemconfigure(
            self.level_text,
            text=f"LEVEL {self.level}"
        )

        self.canvas.itemconfigure(
            self.combo_text,
            text=f"COMBO x{self.combo}"
        )

    def create_blocks(self):
        blocks = []

        columns = BLOCK_COLUMNS
        rows = min(4 + self.level, 8)

        total_width = (
            columns * BLOCK_W
            + (columns - 1) * BLOCK_GAP_X
        )

        start_x = (WIDTH - total_width) // 2
        start_y = HUD_H + 30

        for row in range(rows):
            for col in range(columns):
                x = start_x + col * (BLOCK_W + BLOCK_GAP_X)
                y = start_y + row * (BLOCK_H + BLOCK_GAP_Y)

                blocks.append(
                    Block(self.canvas, x, y, self.level)
                )

        return blocks

    def draw_menu(self):
        self.canvas.create_rectangle(
            150, 200, 750, 450,
            fill=PANEL,
            outline=ACCENT,
            width=2,
            tags="menu"
        )

        self.canvas.create_text(
            WIDTH // 2, 255,
            text="BRICK BREAKER",
            fill=PINK_TEXT,
            font=("Consolas", 34, "bold"),
            tags="menu"
        )

        self.canvas.create_text(
            WIDTH // 2, 315,
            text="BREAK THE BLOCKS. BEAT YOUR HIGH SCORE.",
            fill=GREEN_TEXT,
            font=("Consolas", 10),
            tags="menu"
        )

        self.canvas.create_text(
            WIDTH // 2, 365,
            text="[ ENTER ] START GAME",
            fill=RED_TEXT,
            font=("Consolas", 14, "bold"),
            tags="menu"
        )

        self.canvas.create_text(
            WIDTH // 2, 410,
            text="ARROW KEYS / A-D : MOVE     P : PAUSE     R : RESTART",
            fill=TEXT,
            font=("Consolas", 9),
            tags="menu"
        )

    def show_overlay(self, title, subtitle):
        self.canvas.delete("overlay")

        self.canvas.create_rectangle(
            200, 260, 700, 380,
            fill=PANEL,
            outline=ACCENT,
            width=2,
            tags="overlay"
        )

        self.canvas.create_text(
            WIDTH // 2, 305,
            text=title,
            fill=PINK_TEXT,
            font=("Consolas", 26, "bold"),
            tags="overlay"
        )

        self.canvas.create_text(
            WIDTH // 2, 348,
            text=subtitle,
            fill=TEXT,
            font=("Consolas", 11),
            tags="overlay"
        )

    def key_down(self, event):
        key = event.keysym.lower()
        self.keys.add(key)

        if key in ("return", "space"):
            if self.state == "menu":
                self.start_game()
            elif self.state == "paused":
                # Lanjut dari pause, tanpa suara mulai
                self.start_game(sound=False)
            elif self.state in ("gameover", "won"):
                self.reset_game()
                self.start_game()

        elif key == "p":
            self.toggle_pause()

        elif key == "r":
            self.reset_game()
            self.start_game()

    def key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def start_game(self, sound=True):
        if self.state == "menu":
            self.canvas.delete("menu")

        self.canvas.delete("overlay")
        self.state = "playing"

        if sound:
            self.play_sound("start")

        self.game_loop()

    def toggle_pause(self):
        if self.state == "playing":
            self.state = "paused"
            self.show_overlay(
                "PAUSED",
                "Press P or ENTER to continue"
            )

        elif self.state == "paused":
            self.start_game(sound=False)

    def collision(self, a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b

        return (
            ax1 < bx2 and ax2 > bx1
            and ay1 < by2 and ay2 > by1
        )

    # Bola jatuh melewati striker: langsung game over
    def game_over(self):
        self.state = "gameover"
        self.combo = 0
        self.high_score = max(self.high_score, self.score)
        save_high_score(self.high_score)
        self.play_sound("game_over")
        self.show_overlay(
            "GAME OVER",
            f"SCORE: {self.score}  |  Press ENTER to retry"
        )
        self.update_hud()

    def update_game(self):
        direction = 0

        if "left" in self.keys or "a" in self.keys:
            direction -= 1

        if "right" in self.keys or "d" in self.keys:
            direction += 1

        self.paddle.update(direction)

        if self.ball.update():
            self.game_over()
            return

        ball_rect = (
            self.ball.x - self.ball.radius,
            self.ball.y - self.ball.radius,
            self.ball.x + self.ball.radius,
            self.ball.y + self.ball.radius
        )

        # Collision with paddle
        if self.collision(
            ball_rect,
            self.paddle.get_rect()
        ) and self.ball.dy > 0:

            self.ball.y = (
                self.paddle.y - self.ball.radius - 1
            )
            self.ball.bounce_paddle(self.paddle)

        # Collision with blocks
        for block in self.blocks[:]:
            if self.collision(ball_rect, block.get_rect()):
                self.ball.bounce_block(block)

                if block.hit():
                    self.blocks.remove(block)

                    self.combo += 1
                    self.combo_timer = 100

                    gained = 10 + min(
                        self.combo - 1, 10
                    ) * 2

                    self.score += gained

                    for _ in range(10):
                        self.particles.append(
                            Particle(
                                self.canvas,
                                block.x + block.width // 2,
                                block.y + block.height // 2,
                                block.color
                            )
                        )
                else:
                    self.combo = 0

                break

        # Combo timer
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0

        # Update particles
        for particle in self.particles[:]:
            if not particle.update():
                self.particles.remove(particle)

        # Next level
        if not self.blocks:
            self.level += 1

            self.canvas.delete(self.paddle.id)
            self.canvas.delete(self.ball.id)

            self.paddle = Striker(self.canvas)
            self.ball = Ball(self.canvas, self.level)
            self.blocks = self.create_blocks()

            self.combo = 0

            self.play_sound("level_clear")
            self.show_overlay(
                f"LEVEL {self.level}",
                "Press ENTER to continue"
            )

            self.state = "levelup"

        self.update_hud()

    def game_loop(self):
        if self.state != "playing":
            return

        self.update_game()

        if self.state == "playing":
            self.root.after(FPS, self.game_loop)

        elif self.state == "levelup":
            self.state = "paused"

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    game = BrickBreaker(root)
    game.run()