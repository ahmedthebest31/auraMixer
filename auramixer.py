import pygame
import os
import sys
import random
import atexit
import platform
import tkinter as tk
from tkinter import messagebox

# --- Single Instance Check (Cross-Platform) ---
# This section ensures that only one instance of Auramixer can run at a time.
# It uses a lock file containing the process ID (PID).

def setup_single_instance_lock():
    """
    Establishes a lock file to ensure single-instance operation.
    If another instance is running, it shows a message and exits.
    Handles stale lock files by checking if the PID is still active.
    """
    lock_file_path = os.path.join(os.path.expanduser("~"), ".auramixer.lock")

    def is_process_alive(pid):
        """Cross-platform check if a process with the given PID is alive."""
        if platform.system() == "Windows":
            # On Windows, os.kill doesn't exist. We can use tasklist.
            # Using tasklist is less intrusive and avoids permission issues.
            try:
                import subprocess
                # CREATE_NO_WINDOW flag to prevent console window from flashing.
                output = subprocess.check_output(
                    f'tasklist /FI "PID eq {pid}"',
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000
                )
                return str(pid) in str(output)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False # tasklist not found or other error
        else: # macOS, Linux
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    if os.path.exists(lock_file_path):
        try:
            with open(lock_file_path, "r") as f:
                pid = int(f.read().strip())
            
            if is_process_alive(pid):
                # Show a native OS dialog for accessibility and exit.
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Auramixer Error", "Another instance of Auramixer is already running.")
                root.destroy()
                sys.exit(1)
            else:
                # Stale lock file, remove it.
                os.remove(lock_file_path)
        except (IOError, ValueError):
            # Corrupt lock file, try to remove it.
            try:
                os.remove(lock_file_path)
            except OSError:
                pass # Ignore if it's already gone.

    # Create a new lock file for the current instance.
    with open(lock_file_path, "w") as f:
        f.write(str(os.getpid()))
    
    # Register cleanup to remove the lock file on normal exit.
    def _cleanup_lock_file():
        """Ensures the lock file is removed on exit."""
        try:
            os.remove(lock_file_path)
        except OSError:
            pass
    
    atexit.register(_cleanup_lock_file)

# --- Main Application Setup ---

def get_absolute_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def load_all_assets():
    """
    Loads all media assets (backgrounds, effects, music).
    Creates folders if they don't exist.
    Returns loaded assets and a boolean indicating if there was a media error.
    """
    media_error = False
    
    # Define paths and ensure folders exist
    backgrounds_path = get_absolute_path("backgrounds")
    effects_path = get_absolute_path("effects")
    music_path = get_absolute_path("music")
    
    os.makedirs(backgrounds_path, exist_ok=True)
    os.makedirs(effects_path, exist_ok=True)
    os.makedirs(music_path, exist_ok=True)

    # Load Backgrounds
    background_images = []
    valid_bg_ext = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
    try:
        for f in os.listdir(backgrounds_path):
            if f.lower().endswith(valid_bg_ext):
                try:
                    img = pygame.image.load(os.path.join(backgrounds_path, f)).convert()
                    background_images.append(img)
                except pygame.error:
                    continue # Skip corrupted files
    except OSError:
        media_error = True
    if not background_images:
        media_error = True

    # Load Effects
    effect_sounds = []
    valid_audio_ext = ('.wav', '.mp3', '.ogg')
    try:
        for f in os.listdir(effects_path):
            if f.lower().endswith(valid_audio_ext):
                try:
                    sound = pygame.mixer.Sound(os.path.join(effects_path, f))
                    effect_sounds.append(sound)
                except pygame.error:
                    continue
    except OSError:
        media_error = True
    if not effect_sounds:
        media_error = True

    # Load Music
    music_files = []
    try:
        for f in os.listdir(music_path):
            if f.lower().endswith(valid_audio_ext):
                # For music, we load the path to stream, not the whole file into memory
                music_files.append(os.path.join(music_path, f))
    except OSError:
        media_error = True
    if not music_files:
        media_error = True
        
    assets = {
        "backgrounds": background_images,
        "effects": effect_sounds,
        "music": music_files
    }
    
    return assets, media_error

def show_media_error_screen(screen):
    """
    Displays a fullscreen error message and waits for user to press 'R' to reload or quit.
    Also shows a native OS warning dialog for accessibility.
    """
    # 1. Show native OS dialog for accessibility (e.g., screen readers)
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning(
        "Auramixer - Media Missing",
        "Auramixer is missing media files. Please add images to 'backgrounds', sounds to 'effects', and music to 'music'. Then press [R] to reload."
    )
    root.destroy()

    # 2. Show fullscreen Pygame warning
    screen_width, screen_height = screen.get_size()
    error_font = pygame.font.Font(None, 48)
    
    message_lines = [
        "Auramixer is missing media files.",
        "Please add images to 'backgrounds', sounds to 'effects',",
        "and music to 'music'.",
        "",
        "Press [R] to reload or [ESC] to quit."
    ]
    
    rendered_texts = [error_font.render(line, True, (255, 255, 255)) for line in message_lines]
    
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False # Quit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True # Reload
                if event.key == pygame.K_ESCAPE:
                    return False # Quit

        screen.fill((0, 0, 0)) # Black background
        
        # Calculate total height and draw text centered
        total_height = sum(text.get_height() for text in rendered_texts) + (len(rendered_texts) * 10)
        current_y = (screen_height - total_height) // 2
        
        for text_surface in rendered_texts:
            text_rect = text_surface.get_rect(center=(screen_width // 2, current_y + text_surface.get_height() // 2))
            screen.blit(text_surface, text_rect)
            current_y += text_surface.get_height() + 10
            
        pygame.display.flip()
        pygame.time.wait(100) # Reduce CPU usage
        
    return False

def run_main_program(screen, assets):
    """
    The main application logic, runs when all media is successfully loaded.
    """
    # --- Unpack Assets ---
    all_background_images = assets["backgrounds"]
    effect_sounds = assets["effects"]
    music_files = assets["music"]

    # --- Screen & Font ---
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    font = pygame.font.Font(None, 36)
    
    # --- UI State ---
    show_text = False

    # --- Image Scaling ---
    def scale_and_crop_image(original_image):
        img_aspect = original_image.get_width() / original_image.get_height()
        screen_aspect = SCREEN_WIDTH / SCREEN_HEIGHT
        if img_aspect > screen_aspect:
            new_height = SCREEN_HEIGHT
            new_width = int(new_height * img_aspect)
        else:
            new_width = SCREEN_WIDTH
            new_height = int(new_width / img_aspect)
        scaled = pygame.transform.scale(original_image, (new_width, new_height))
        x_offset = (new_width - SCREEN_WIDTH) // 2
        y_offset = (new_height - SCREEN_HEIGHT) // 2
        return scaled.subsurface(pygame.Rect(x_offset, y_offset, SCREEN_WIDTH, SCREEN_HEIGHT))

    scaled_backgrounds = [scale_and_crop_image(img) for img in all_background_images]
    current_bg_index = 0
    current_display_image = scaled_backgrounds[current_bg_index]
    target_display_image = None
    fade_alpha = 255
    BACKGROUND_CHANGE_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(BACKGROUND_CHANGE_EVENT, 10000)

    # --- Sound Setup ---
    effect_map = {pygame.K_a + i: sound for i, sound in enumerate(effect_sounds)}
    
    music_volume = 0.5
    effect_volume = 0.7
    
    def play_effect(key_code):
        if key_code in effect_map:
            effect_map[key_code].set_volume(effect_volume)
            effect_map[key_code].play()

    def play_music(track_index):
        if 0 <= track_index < len(music_files):
            pygame.mixer.music.load(music_files[track_index])
            pygame.mixer.music.set_volume(music_volume)
            pygame.mixer.music.play(-1, fade_ms=2000)

    def stop_all_sounds():
        pygame.mixer.music.fadeout(2000)
        pygame.mixer.stop() # Stops all sound effects immediately

    # --- Main Loop ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    stop_all_sounds()
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    show_text = not show_text
                elif pygame.K_a <= event.key <= pygame.K_z:
                    play_effect(event.key)
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    play_music(event.key - pygame.K_1)
                elif event.key == pygame.K_0:
                    play_music(9) # 10th track
                elif event.key == pygame.K_UP:
                    music_volume = min(1.0, music_volume + 0.1)
                    pygame.mixer.music.set_volume(music_volume)
                elif event.key == pygame.K_DOWN:
                    music_volume = max(0.0, music_volume - 0.1)
                    pygame.mixer.music.set_volume(music_volume)
                elif event.key == pygame.K_RIGHT:
                    effect_volume = min(1.0, effect_volume + 0.1)
                elif event.key == pygame.K_LEFT:
                    effect_volume = max(0.0, effect_volume - 0.1)
            
            if event.type == BACKGROUND_CHANGE_EVENT:
                current_bg_index = (current_bg_index + 1) % len(scaled_backgrounds)
                target_display_image = scaled_backgrounds[current_bg_index]
                fade_alpha = 0

        # --- Drawing ---
        if target_display_image and fade_alpha < 255:
            fade_alpha = min(255, fade_alpha + 5)
            current_display_image.set_alpha(255 - fade_alpha)
            screen.blit(current_display_image, (0, 0))
            target_display_image.set_alpha(fade_alpha)
            screen.blit(target_display_image, (0, 0))
            if fade_alpha >= 255:
                current_display_image = target_display_image
                target_display_image = None
        else:
            screen.blit(current_display_image, (0, 0))

        # --- Help Text ---
        if show_text:
            help_text = [
                "Auramixer Controls:",
                "ESC: Quit",
                "1-0: Play Music Track",
                "A-Z: Play Sound Effect",
                "SPACE: Stop All Music & Effects",
                "UP/DOWN: Music Volume",
                "LEFT/RIGHT: Effect Volume",
                "SHIFT: Toggle This Help"
            ]
            y_pos = 20
            for line in help_text:
                text_surf = font.render(line, True, (255, 255, 0), (0, 0, 0))
                screen.blit(text_surf, (20, y_pos))
                y_pos += 30

        pygame.display.flip()
        pygame.time.Clock().tick(60)

def main():
    """
    Main function to initialize and run the application.
    """
    # 1. Ensure only one instance is running
    setup_single_instance_lock()

    # 2. Initialize Pygame
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption("Auramixer")
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    # 3. Main application loop (allows for reloading)
    while True:
        assets, media_error = load_all_assets()
        
        if media_error:
            should_reload = show_media_error_screen(screen)
            if not should_reload:
                break # User chose to quit
        else:
            run_main_program(screen, assets)
            break # Main program finished, so exit the loop

    # 4. Quit
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()