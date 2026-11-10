import tkinter as tk
import random

# Dimensions of the screen
WIDTH, HEIGHT = 600, 500

# Colors (pastel)
BG = "#1f1d36"
PANEL = "#2b2850"
TEXT = "#fdf6ff"
GRID = "#2a2748"
RED = "#ff9aa8"
YELLOW = "#fff3a8"

PINK = "#ffb3c6"
PEACH = "#ffcfa3"
MINT = "#b5ead7"
SKY = "#a8d8ff"
LAVENDER = "#d4bfff"

# The 5 colors of the blocks. The block with STRONG_COLOR has the
# health of 200, so the ball must hit it twice to break
BLOCK_COLORS = [PINK, PEACH, MINT, SKY, LAVENDER]
STRONG_COLOR = LAVENDER

FPS = 30
FONT = ("Consolas", 12, "bold")


# Striker class
class Striker:
    def __init__(self, canvas, posx, posy, width, height, speed, color):
        self.canvas = canvas
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.speed = speed
        self.color = color

        # The rect variable is used to handle the placement
        # and the collisions of the object
        self.strikerRect = (self.posx, self.posy,
                            self.posx + self.width, self.posy + self.height)
        self.striker = canvas.create_rectangle(
            *self.strikerRect, fill=self.color, outline=TEXT, width=2)

    # Used to render the object on the screen
    def display(self):
        self.canvas.coords(self.striker, *self.strikerRect)

    # Used to update the state of the object
    def update(self, xFac):
        self.posx += self.speed * xFac

        # Restricting the striker to be in between the
        # left and right edges of the screen
        if self.posx <= 0:
            self.posx = 0
        elif self.posx + self.width >= WIDTH:
            self.posx = WIDTH - self.width

        self.strikerRect = (self.posx, self.posy,
                            self.posx + self.width, self.posy + self.height)

    # Returns the rect of the object
    def getRect(self):
        return self.strikerRect


# Block Class
class Block:
    def __init__(self, canvas, posx, posy, width, height, color):
        self.canvas = canvas
        self.posx, self.posy = posx, posy
        self.width, self.height = width, height
        self.color = color
        self.damage = 100

        # The strong blocks have the health of 200. So,
        # the ball must hit it twice to break
        if color == STRONG_COLOR:
            self.health = 200
            outline, outlineWidth = TEXT, 2
        else:
            self.health = 100
            outline, outlineWidth = BG, 1
        self.maxHealth = self.health

        self.blockRect = (self.posx, self.posy,
                          self.posx + self.width, self.posy + self.height)
        self.block = canvas.create_rectangle(
            *self.blockRect, fill=self.color,
            outline=outline, width=outlineWidth)

    # Used to render the object on the screen if and only
    # if its health is greater than 0
    def display(self):
        if self.health > 0:
            if self.health < self.maxHealth:
                self.canvas.itemconfigure(self.block, fill=YELLOW)
            else:
                self.canvas.itemconfigure(self.block, fill=self.color)

    # Used to decrease the health of the block
    def hit(self):
        self.health -= self.damage

    # Used to remove the block from the canvas
    def destroy(self):
        self.canvas.delete(self.block)

    # Used to get the rect of the object
    def getRect(self):
        return self.blockRect

    # Used to get the health of the object
    def getHealth(self):
        return self.health


# Ball Class
class Ball:
    def __init__(self, canvas, posx, posy, radius, speed, color):
        self.canvas = canvas
        self.startx, self.starty = posx, posy
        self.posx, self.posy = posx, posy
        self.radius = radius
        self.speed = speed
        self.color = color
        self.xFac, self.yFac = random.choice([-1, 1]), -1

        self.ball = canvas.create_oval(
            *self.getRect(), fill=self.color, outline=TEXT, width=2)

    # Used to display the object on the screen
    def display(self):
        self.canvas.coords(self.ball, *self.getRect())

    # Used to update the state of the object
    def update(self):
        self.posx += self.xFac * self.speed
        self.posy += self.yFac * self.speed

        # Reflecting the ball if it touches
        # either of the vertical edges
        if self.posx - self.radius <= 0:
            self.posx = self.radius
            self.xFac = abs(self.xFac)
        elif self.posx + self.radius >= WIDTH:
            self.posx = WIDTH - self.radius
            self.xFac = -abs(self.xFac)

        # Reflection from the top most edge of the screen
        if self.posy - self.radius <= 0:
            self.posy = self.radius
            self.yFac = abs(self.yFac)

        # If the ball falls below the bottom edge of
        # the screen, True value is returned
        if self.posy - self.radius > HEIGHT:
            return True

        return False

    # Resets the position of the ball
    def reset(self):
        self.posx, self.posy = self.startx, self.starty
        self.xFac, self.yFac = random.choice([-1, 1]), -1

    # Used to change the direction of the ball. Without a rect,
    # only the Y direction is flipped. With the rect of a block,
    # the side that was hit decides which direction is flipped
    def hit(self, rect=None):
        if rect is None:
            self.yFac *= -1
            return

        x1, y1, x2, y2 = rect
        overlapX = min(self.posx + self.radius - x1,
                       x2 - (self.posx - self.radius))
        overlapY = min(self.posy + self.radius - y1,
                       y2 - (self.posy - self.radius))

        if overlapX < overlapY:
            self.xFac *= -1
        else:
            self.yFac *= -1

    # Bounce on the striker: the farther from the center
    # the ball lands, the more it is pushed sideways
    def hitStriker(self, striker):
        offset = (self.posx - (striker.posx + striker.width / 2)) \
            / (striker.width / 2)
        xFac = max(-1.5, min(1.5, offset * 1.5))

        if abs(xFac) < 0.3:
            xFac = 0.3 if xFac >= 0 else -0.3

        self.xFac = xFac
        self.yFac = -1
        self.posy = striker.posy - self.radius - 1

    # Returns the rect of the ball
    def getRect(self):
        return (self.posx - self.radius, self.posy - self.radius,
                self.posx + self.radius, self.posy + self.radius)


# Helper Functions

# Function used to check collisions between any two entities
def collisionChecker(rect, ball):
    ax1, ay1, ax2, ay2 = rect
    bx1, by1, bx2, by2 = ball

    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1


# Function used to populate the blocks
def populateBlocks(canvas, blockWidth, blockHeight,
                   horizontalGap, verticalGap):
    listOfBlocks = []

    columns = (WIDTH + horizontalGap) // (blockWidth + horizontalGap)
    startX = (WIDTH - (columns * blockWidth
                       + (columns - 1) * horizontalGap)) // 2

    for i in range(startX, WIDTH - blockWidth + 1,
                   blockWidth + horizontalGap):
        for j in range(30, HEIGHT // 2, blockHeight + verticalGap):
            listOfBlocks.append(
                Block(canvas, i, j, blockWidth, blockHeight,
                      random.choice(BLOCK_COLORS)))

    return listOfBlocks


# Function used to draw the grid in the background
def drawBackground(canvas):
    for x in range(0, WIDTH, 40):
        canvas.create_line(x, 0, x, HEIGHT, fill=GRID)

    for y in range(0, HEIGHT, 40):
        canvas.create_line(0, y, WIDTH, y, fill=GRID)


# Once all the lives are over, this function shows the
# game over message. The game restarts when space bar is pressed
def gameOver(canvas, score):
    canvas.create_rectangle(100, 170, 500, 310, fill=PANEL,
                            outline=SKY, width=2, tags="overlay")
    canvas.create_text(WIDTH // 2, 215, text="GAME OVER", fill=RED,
                       font=("Consolas", 30, "bold"), tags="overlay")
    canvas.create_text(WIDTH // 2, 255, text="Score : " + str(score),
                       fill=TEXT, font=("Consolas", 14), tags="overlay")
    canvas.create_text(WIDTH // 2, 285, text="Press SPACE to play again",
                       fill=YELLOW, font=("Consolas", 11), tags="overlay")


# Game Manager
def main():
    root = tk.Tk()
    root.title("Pastel Block Breaker")
    root.resizable(False, False)

    canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                       bg=BG, highlightthickness=0)
    canvas.pack()
    drawBackground(canvas)

    running = True
    lives = 3
    score = 0

    scoreText = canvas.create_text(10, HEIGHT - 12, text="Score : 0",
                                   fill=TEXT, font=FONT, anchor="w")
    livesText = canvas.create_text(150, HEIGHT - 12, text="Lives : 3",
                                   fill=TEXT, font=FONT, anchor="w")

    striker = Striker(canvas, WIDTH // 2 - 50, HEIGHT - 50, 100, 14, 10, TEXT)
    strikerXFac = 0

    ball = Ball(canvas, WIDTH // 2, HEIGHT - 80, 7, 5, YELLOW)

    blockWidth, blockHeight = 40, 15
    horizontalGap, verticalGap = 20, 20

    listOfBlocks = populateBlocks(
        canvas, blockWidth, blockHeight, horizontalGap, verticalGap)

    # Blocks are created after the ball, so the ball and
    # the striker are brought to the front again
    canvas.tag_raise(striker.striker)
    canvas.tag_raise(ball.ball)

    pressed = set()

    # Event handling
    def keyDown(event):
        nonlocal strikerXFac
        pressed.add(event.keysym.lower())

        strikerXFac = 0
        if "left" in pressed or "a" in pressed:
            strikerXFac -= 1
        if "right" in pressed or "d" in pressed:
            strikerXFac += 1

        if event.keysym == "space" and not running:
            newGame()

    def keyUp(event):
        nonlocal strikerXFac
        pressed.discard(event.keysym.lower())

        strikerXFac = 0
        if "left" in pressed or "a" in pressed:
            strikerXFac -= 1
        if "right" in pressed or "d" in pressed:
            strikerXFac += 1

    # Starts a new game after the game over
    def newGame():
        nonlocal running, lives, score, listOfBlocks

        for block in listOfBlocks:
            block.destroy()

        canvas.delete("overlay")

        lives = 3
        score = 0
        listOfBlocks = populateBlocks(
            canvas, blockWidth, blockHeight, horizontalGap, verticalGap)
        canvas.tag_raise(striker.striker)
        canvas.tag_raise(ball.ball)

        ball.reset()
        running = True
        gameLoop()

    # Game loop
    def gameLoop():
        nonlocal running, lives, score, listOfBlocks

        if not running:
            return

        # If all the blocks are destroyed, then we repopulate them
        if not listOfBlocks:
            listOfBlocks = populateBlocks(
                canvas, blockWidth, blockHeight, horizontalGap, verticalGap)
            canvas.tag_raise(striker.striker)
            canvas.tag_raise(ball.ball)

        # Collision check
        if collisionChecker(striker.getRect(), ball.getRect()) \
                and ball.yFac > 0:
            ball.hitStriker(striker)

        for block in listOfBlocks:
            if collisionChecker(block.getRect(), ball.getRect()):
                ball.hit(block.getRect())
                block.hit()

                if block.getHealth() <= 0:
                    block.destroy()
                    listOfBlocks.remove(block)
                    score += 5

                break

        # Update
        striker.update(strikerXFac)
        lifeLost = ball.update()

        if lifeLost:
            lives -= 1
            ball.reset()

        # Display
        striker.display()
        ball.display()

        for block in listOfBlocks:
            block.display()

        canvas.itemconfigure(scoreText, text="Score : " + str(score))
        canvas.itemconfigure(livesText, text="Lives : " + str(lives))

        # All the lives are over. So, the gameOver() function is called
        if lives <= 0:
            running = False
            gameOver(canvas, score)
            return

        root.after(1000 // FPS, gameLoop)

    root.bind("<KeyPress>", keyDown)
    root.bind("<KeyRelease>", keyUp)

    gameLoop()
    root.mainloop()


if __name__ == "__main__":
    main()