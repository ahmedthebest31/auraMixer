# -*- coding: utf-8 -*-

import pygame
import os
import sys
import random
import atexit
import platform
import tkinter as tk
from tkinter import messagebox
import accessible_output2.outputs.auto

# --- Configuration ---
IS_PORTABLE = True
CROSSFADE_DURATION_MS = 2000 # Duration for fade-in and fade-out

# --- Single Instance Check ---
def setup_single_instance_lock():
    lock_file_path = os.path.join(os.path.expanduser("~"), ".auramixer.lock")

    def is_process_alive(pid):
        if platform.system() == "Windows":
            try:
                import subprocess
                output = subprocess.check_output(
                    f'tasklist /FI "PID eq {pid}"', stderr=subprocess.DEVNULL, creationflags=0x08000000)
                return str(pid) in str(output)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False
        else:
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
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Auramixer Error", "Another instance of Auramixer is already running.")
                root.destroy()
                sys.exit(1)
            else:
                os.remove(lock_file_path)
        except (IOError, ValueError):
            try:
                os.remove(lock_file_path)
            except OSError:
                pass

    with open(lock_file_path, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.remove(lock_file_path) if os.path.exists(lock_file_path) else None)
    
# a func that used to speak text with the running screen reader
# do to pygame isn't accessible
# we will use this to read the help text
# Initialize the output handler once (global)
_output_handler = accessible_output2.outputs.auto.Auto()

def speak(text: str, interrupt: bool = True):
    """
    Speaks or brailles the given text using Accessible Output 2.

    Parameters:
        text (str): The text to speak or braille.
        interrupt (bool, optional): Whether to interrupt current speech. Default is True.

    Usage:
        speak("Hello world")                # speaks and interrupts
        speak("Next line", interrupt=False) # speaks without interrupting
    """
    if not isinstance(text, str):
        raise TypeError("Text must be a string.")

    # Accessible Output 2: speak the text
    _output_handler.speak(text, interrupt=interrupt)

# --- Path and Asset Management ---
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_asset_paths(is_portable):
    needs_user_notification = False
    if is_portable:
        base_path = os.path.dirname(sys.executable) if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
    else:
        documents_path = os.path.join(os.path.expanduser('~'), 'Documents')
        base_path = os.path.join(documents_path, 'Auramixer')
        if not os.path.exists(base_path):
            needs_user_notification = True

    paths = {
        "base": base_path,
        "backgrounds": os.path.join(base_path, "backgrounds"),
        "effects": os.path.join(base_path, "effects"),
        "music": os.path.join(base_path, "music")
    }
    for path_key in ["backgrounds", "effects", "music"]:
        os.makedirs(paths[path_key], exist_ok=True)
    return paths, needs_user_notification

def load_all_assets(asset_paths):
    missing_asset_types = []
    backgrounds_path = asset_paths["backgrounds"]
    effects_path = asset_paths["effects"]
    music_path = asset_paths["music"]
    valid_audio_ext = ('.wav', '.mp3', '.ogg')

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
                    continue
    except OSError:
        pass # Handled by the check below

    if not background_images:
        missing_asset_types.append('backgrounds')

    # Load Effects
    effect_sounds = []
    try:
        for f in os.listdir(effects_path):
            if f.lower().endswith(valid_audio_ext):
                try:
                    sound = pygame.mixer.Sound(os.path.join(effects_path, f))
                    effect_sounds.append(sound)
                except pygame.error:
                    continue
    except OSError:
        pass

    if not effect_sounds:
        missing_asset_types.append('effects')
    
    # Load Music
    music_sounds = []
    try:
        for f in os.listdir(music_path):
            if f.lower().endswith(valid_audio_ext):
                try:
                    sound = pygame.mixer.Sound(os.path.join(music_path, f))
                    music_sounds.append(sound)
                except pygame.error:
                    continue
    except OSError:
        pass

    if not music_sounds:
        missing_asset_types.append('music')
        
    assets = {
        "backgrounds": background_images,
        "effects": effect_sounds,
        "music": music_sounds
    }
    
    # A fatal error only occurs if essential audio is missing.
    is_fatal_error = 'music' in missing_asset_types or 'effects' in missing_asset_types
    
    return assets, is_fatal_error, missing_asset_types

def show_media_error_screen(screen, asset_paths, is_portable):
    base_path = asset_paths['base']
    location_string = f"the folders next to the application.\n\nPath: {base_path}" if is_portable else f"the 'Auramixer' folder in your Documents.\n\nPath: {base_path}"
    root = tk.Tk()
    root.withdraw()
    messagebox.showwarning(
        "Auramixer - Essential Files Missing", 
        f"Essential audio files are missing from the 'music' or 'effects' folders. Please add audio files to {location_string}\n\nThen press [R] to reload."
    )
    root.destroy()

    screen_width, screen_height = screen.get_size()
    error_font = pygame.font.Font(None, 48)
    message_lines = ["Essential audio files are missing.", "Please check the 'music' and 'effects' folders.", "", "Press [R] to reload or [ESC] to quit."]
    rendered_texts = [error_font.render(line, True, (255, 255, 255)) for line in message_lines]
    
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r: return True
                if event.key == pygame.K_ESCAPE: return False
        screen.fill((0, 0, 0))
        total_height = sum(text.get_height() for text in rendered_texts) + (len(rendered_texts) * 10)
        current_y = (screen_height - total_height) // 2
        for text_surface in rendered_texts:
            text_rect = text_surface.get_rect(center=(screen_width // 2, current_y + text_surface.get_height() // 2))
            screen.blit(text_surface, text_rect)
            current_y += text_surface.get_height() + 10
        pygame.display.flip()
        pygame.time.wait(100)
    return False

def run_main_program(screen, assets):
    all_background_images = assets["backgrounds"]
    effect_sounds = assets["effects"]
    music_sounds = assets["music"]

    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    show_text = False

    def scale_and_crop_image(img):
        img_aspect, screen_aspect = img.get_width() / img.get_height(), SCREEN_WIDTH / SCREEN_HEIGHT
        new_width, new_height = (int(SCREEN_HEIGHT * img_aspect), SCREEN_HEIGHT) if img_aspect > screen_aspect else (SCREEN_WIDTH, int(SCREEN_WIDTH / img_aspect))
        scaled = pygame.transform.scale(img, (new_width, new_height))
        x_offset, y_offset = (new_width - SCREEN_WIDTH) // 2, (new_height - SCREEN_HEIGHT) // 2
        return scaled.subsurface(pygame.Rect(x_offset, y_offset, SCREEN_WIDTH, SCREEN_HEIGHT))

    scaled_backgrounds = [scale_and_crop_image(img) for img in all_background_images]
    current_bg_index, current_display_image, target_display_image, fade_alpha = 0, scaled_backgrounds[0], None, 255
    BACKGROUND_CHANGE_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(BACKGROUND_CHANGE_EVENT, 10000)

    # --- Advanced Audio Engine for Crossfading ---
    effect_map = {pygame.K_a + i: sound for i, sound in enumerate(effect_sounds)}
    music_volume, effect_volume = 0.5, 0.7

    # Reserve two channels for music crossfading
    music_channel1 = pygame.mixer.Channel(0)
    music_channel2 = pygame.mixer.Channel(1)
    active_music_channel = music_channel1
    current_music_index = None

    def play_music(track_index):
        nonlocal active_music_channel, current_music_index
        if track_index == current_music_index or not (0 <= track_index < len(music_sounds)):
            return

        inactive_music_channel = music_channel2 if active_music_channel == music_channel1 else music_channel1
        
        # Fade out the old track
        if inactive_music_channel.get_sound():
            inactive_music_channel.fadeout(CROSSFADE_DURATION_MS)

        # Play new track on the now-active channel with a fade-in
        sound_to_play = music_sounds[track_index]
        active_music_channel.play(sound_to_play, loops=-1, fade_ms=CROSSFADE_DURATION_MS)
        active_music_channel.set_volume(music_volume)
        
        # Swap channels for the next run
        current_music_index = track_index
        active_music_channel = inactive_music_channel

    def stop_all_sounds():
        nonlocal current_music_index
        music_channel1.fadeout(CROSSFADE_DURATION_MS)
        music_channel2.fadeout(CROSSFADE_DURATION_MS)
        current_music_index = None

        # Fade out all other active channels (sound effects)
        for i in range(2, pygame.mixer.get_num_channels()):
            channel = pygame.mixer.Channel(i)
            if channel.get_busy():
                channel.fadeout(1000) # Fade out effects over 1 second

    def play_effect(key_code):
        if key_code in effect_map:
            effect_map[key_code].set_volume(effect_volume)
            effect_map[key_code].play()

    # --- Help Screen ---
    def draw_help_screen(surface):
        # (Help screen drawing code remains the same)
        title_font, text_font, white = pygame.font.Font(None, 52), pygame.font.Font(None, 34), (255, 255, 255)
        help_items = [("Auramixer Controls", title_font),("", text_font),("--- General ---", text_font),("SHIFT: Toggle this help", text_font),("ESC: Quit Program", text_font),("R: Reload (on media error screen)", text_font),("", text_font),("--- Audio Control ---", text_font),("1-0 / Numpad 1-0: Play Music Track", text_font),("A-Z: Play Sound Effect", text_font),("SPACE: Stop All Music & Effects", text_font),("UP/DOWN Arrow: Adjust Music Volume", text_font),("LEFT/RIGHT Arrow: Adjust Effect Volume", text_font)]
        rendered_lines = [font.render(text, True, white) for text, font in help_items]
        padding, max_width, total_height = 25, max(line.get_width() for line in rendered_lines), sum(line.get_height() for line in rendered_lines)
        panel_width, panel_height = max_width + padding * 2, total_height + padding * 2
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA); panel.fill((0, 0, 0, 180))
        current_y = padding
        for line in rendered_lines:
            panel.blit(line, ((panel_width - line.get_width()) // 2, current_y)); current_y += line.get_height()
        surface.blit(panel, ((surface.get_width() - panel_width) // 2, (surface.get_height() - panel_height) // 2))
        speak("""
Auramixer Controls
--- General ---
SHIFT: Toggle this help
ESC: Quit Program
R: Reload (on media error screen)
--- Audio Control ---
1-0 / Numpad 1-0: Play Music Track
A-Z: Play Sound Effect
SPACE: Stop All Music & Effects
UP/DOWN Arrow: Adjust Music Volume
LEFT/RIGHT Arrow: Adjust Effect Volume
""")

    # --- Main Loop ---
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_SPACE: stop_all_sounds()
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT): show_text = not show_text
                elif pygame.K_a <= event.key <= pygame.K_z: play_effect(event.key)
                elif pygame.K_1 <= event.key <= pygame.K_9: play_music(event.key - pygame.K_1)
                elif event.key == pygame.K_0: play_music(9)
                elif pygame.K_KP1 <= event.key <= pygame.K_KP9: play_music(event.key - pygame.K_KP1)
                elif event.key == pygame.K_KP0: play_music(9)
                elif event.key == pygame.K_UP:
                    music_volume = min(1.0, round(music_volume + 0.1, 1))
                    music_channel1.set_volume(music_volume); music_channel2.set_volume(music_volume)
                elif event.key == pygame.K_DOWN:
                    music_volume = max(0.0, round(music_volume - 0.1, 1))
                    music_channel1.set_volume(music_volume); music_channel2.set_volume(music_volume)
                elif event.key == pygame.K_RIGHT: effect_volume = min(1.0, round(effect_volume + 0.1, 1))
                elif event.key == pygame.K_LEFT: effect_volume = max(0.0, round(effect_volume - 0.1, 1))
            
            if event.type == BACKGROUND_CHANGE_EVENT:
                current_bg_index = (current_bg_index + 1) % len(scaled_backgrounds)
                target_display_image = scaled_backgrounds[current_bg_index]
                fade_alpha = 0

        # Drawing
        if target_display_image and fade_alpha < 255:
            fade_alpha = min(255, fade_alpha + 5)
            current_display_image.set_alpha(255 - fade_alpha); screen.blit(current_display_image, (0, 0))
            target_display_image.set_alpha(fade_alpha); screen.blit(target_display_image, (0, 0))
            if fade_alpha >= 255: current_display_image = target_display_image; target_display_image = None
        else:
            screen.blit(current_display_image, (0, 0))

        if show_text: draw_help_screen(screen)

        pygame.display.flip()
        clock.tick(60)

def main():
    setup_single_instance_lock()

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.mixer.set_num_channels(32) # More channels for effects
    
    pygame.display.set_caption("Auramixer")
    try:
        icon_surface = pygame.image.load(get_resource_path("assets/icon_64.png"))
        pygame.display.set_icon(icon_surface)
    except Exception: pass
        
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen.fill((0, 0, 0)); pygame.display.flip()

    asset_paths, needs_notification = setup_asset_paths(IS_PORTABLE)

    if needs_notification:
        root = tk.Tk(); root.withdraw()
        messagebox.showinfo("Auramixer Setup", f"A new folder has been created for your media files at:\n\n{asset_paths['base']}\n\nPlease add your files to the subfolders.")
        root.destroy()

    while True:
        assets, is_fatal_error, missing_types = load_all_assets(asset_paths)
        
        # Handle fatal error (missing audio)
        if is_fatal_error:
            if not show_media_error_screen(screen, asset_paths, IS_PORTABLE): 
                break # Quit if user chooses not to reload
            else:
                continue # Loop back to try loading assets again

        # Handle non-fatal warning (missing backgrounds)
        if 'backgrounds' in missing_types:
            root = tk.Tk(); root.withdraw()
            messagebox.showinfo("Auramixer - Backgrounds Missing", f"No images found in the 'backgrounds' folder. Using the default icon as a fallback.\n\nTo see your own images, add them to:\n{asset_paths['backgrounds']}")
            root.destroy()
            
            # Add the fallback background programmatically
            try:
                fallback_img = pygame.image.load(get_resource_path("assets/icon_64.png")).convert()
                assets['backgrounds'].append(fallback_img)
            except Exception:
                black_surface = pygame.Surface((800, 600)); black_surface.fill((0, 0, 0))
                assets['backgrounds'].append(black_surface)

        # If we reach here, we are good to go
        run_main_program(screen, assets)
        break # Exit the while loop after the program finishes normally

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
