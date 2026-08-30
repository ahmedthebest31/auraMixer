import pygame
import os
import sys
import random
import atexit
import platform
import ctypes
import tkinter as tk
from tkinter import messagebox

# --- Configuration ---
IS_PORTABLE = True
CROSSFADE_DURATION_MS = 2000 # Duration for fade-in and fade-out

# --- Single Instance Check ---
def _is_windows_process_alive(pid):
    """Checks whether a Windows process is running using the Win32 API directly.

    Avoids the fragile tasklist text-parsing approach and works regardless of
    the system locale. Returns False if the process does not exist or we
    cannot open it (e.g. it already exited).
    """
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        exit_code = ctypes.c_ulong(0)
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        # STILL_ACTIVE (259) means the process is still running.
        return exit_code.value == 259
    finally:
        kernel32.CloseHandle(handle)

def is_process_alive(pid):
    if platform.system() == "Windows":
        return _is_windows_process_alive(pid)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def setup_single_instance_lock():
    lock_file_path = os.path.join(os.path.expanduser("~"), ".auramixer.lock")

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

# --- Path and Asset Management ---
def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def _get_documents_folder():
    """Returns the real Documents folder, resolving OneDrive redirections.

    Uses the Windows known-folder API when available; otherwise falls back to
    the classic '~/Documents' path.
    """
    if platform.system() == "Windows":
        try:
            shell32 = ctypes.windll.shell32

            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", ctypes.c_ulong),
                    ("Data2", ctypes.c_ushort),
                    ("Data3", ctypes.c_ushort),
                    ("Data4", ctypes.c_ubyte * 8),
                ]

            # FOLDERID_Documents = {FDD39AD0-238F-46AF-ADB4-6C85480369C1}
            folderid = GUID()
            folderid.Data1 = 0xFDD39AD0
            folderid.Data2 = 0x238F
            folderid.Data3 = 0x46AF
            folderid.Data4 = (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC1)

            # Declare signatures so the 64-bit pointer is returned correctly.
            SHGetKnownFolderPath = shell32.SHGetKnownFolderPath
            SHGetKnownFolderPath.argtypes = [
                ctypes.POINTER(GUID), ctypes.c_ulong, ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_wchar_p)]
            SHGetKnownFolderPath.restype = ctypes.c_ulong

            p_path = ctypes.c_wchar_p()
            result = SHGetKnownFolderPath(
                ctypes.byref(folderid), 0, None, ctypes.byref(p_path))
            if result == 0 and p_path.value:
                path = p_path.value
                ctypes.windll.ole32.CoTaskMemFree(p_path)
                return path
        except (AttributeError, OSError, ValueError):
            pass
    return os.path.join(os.path.expanduser("~"), "Documents")

def setup_asset_paths(is_portable):
    needs_user_notification = False
    if is_portable:
        base_path = os.path.dirname(sys.executable) if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
    else:
        documents_path = _get_documents_folder()
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
    valid_audio_ext = ('.wav', '.mp3', '.ogg', '.flac')

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

def run_main_program(screen, load_assets_callback, asset_paths, is_portable):
    SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
    show_text = False

    def scale_and_crop_image(img):
        img_aspect, screen_aspect = img.get_width() / img.get_height(), SCREEN_WIDTH / SCREEN_HEIGHT
        new_width, new_height = (int(SCREEN_HEIGHT * img_aspect), SCREEN_HEIGHT) if img_aspect > screen_aspect else (SCREEN_WIDTH, int(SCREEN_WIDTH / img_aspect))
        scaled = pygame.transform.scale(img, (new_width, new_height))
        x_offset, y_offset = (new_width - SCREEN_WIDTH) // 2, (new_height - SCREEN_HEIGHT) // 2
        return scaled.subsurface(pygame.Rect(x_offset, y_offset, SCREEN_WIDTH, SCREEN_HEIGHT))

    # Mutable per-frame audio state so the live R reload can rebuild it in place.
    state = {
        "scaled_backgrounds": [],
        "effect_map": {},
        "music_sounds": [],
        "current_bg_index": 0,
        "current_display_image": None,
        "target_display_image": None,
        "fade_alpha": 255,
    }

    def refresh_assets():
        """(Re)loads all assets and rebuilds glyph maps / backgrounds in place.

        Used for the initial load and for the live [R] reload. Always guarantees
        at least one valid background so drawing never crashes. Returns True on
        a usable reload, False if essential audio is still missing.
        """
        assets, is_fatal, missing_types = load_assets_callback(asset_paths)
        if is_fatal:
            return False

        if 'backgrounds' in missing_types or not assets["backgrounds"]:
            try:
                fallback_img = pygame.image.load(get_resource_path("assets/icon_64.png")).convert()
                assets["backgrounds"] = [fallback_img]
            except Exception:
                black_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); black_surface.fill((0, 0, 0))
                assets["backgrounds"] = [black_surface]

        scaled_backgrounds = [scale_and_crop_image(img) for img in assets["backgrounds"]]
        state["scaled_backgrounds"] = scaled_backgrounds
        state["effect_map"] = {pygame.K_a + i: sound for i, sound in enumerate(assets["effects"])}
        state["music_sounds"] = assets["music"]
        state["current_bg_index"] = 0
        state["current_display_image"] = scaled_backgrounds[0]
        state["target_display_image"] = None
        state["fade_alpha"] = 255
        if len(assets["effects"]) > 26:
            state["effect_warning"] = (f"Only the first 26 sound effects are mapped to keys "
                                       f"A-Z. {len(assets['effects']) - 26} effect file(s) ignored.")
        else:
            state["effect_warning"] = None
        return True

    BACKGROUND_CHANGE_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(BACKGROUND_CHANGE_EVENT, 10000)

    # --- Advanced Audio Engine for Crossfading ---
    music_volume, effect_volume = 0.5, 0.7

    # Reserve two channels for music crossfading
    music_channel1 = pygame.mixer.Channel(0)
    music_channel2 = pygame.mixer.Channel(1)
    active_music_channel = music_channel1
    current_music_index = None

    def play_music(track_index):
        nonlocal active_music_channel, current_music_index
        music_sounds = state["music_sounds"]
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
        effect_map = state["effect_map"]
        if key_code in effect_map:
            effect_map[key_code].set_volume(effect_volume)
            effect_map[key_code].play()

    # --- Help Screen ---
    def draw_help_screen(surface):
        # (Help screen drawing code remains the same)
        title_font, text_font, white = pygame.font.Font(None, 52), pygame.font.Font(None, 34), (255, 255, 255)
        help_items = [("Auramixer Controls", title_font),("", text_font),("--- General ---", text_font),("SHIFT: Toggle this help", text_font),("ESC: Quit Program", text_font),("R: Reload Music/Effects/Backgrounds", text_font),("", text_font),("--- Audio Control ---", text_font),("1-0 / Numpad 1-0: Play Music Track", text_font),("A-Z: Play Sound Effect", text_font),("SPACE: Stop All Music & Effects", text_font),("UP/DOWN Arrow: Adjust Music Volume", text_font),("LEFT/RIGHT Arrow: Adjust Effect Volume", text_font)]
        rendered_lines = [font.render(text, True, white) for text, font in help_items]
        padding, max_width, total_height = 25, max(line.get_width() for line in rendered_lines), sum(line.get_height() for line in rendered_lines)
        panel_width, panel_height = max_width + padding * 2, total_height + padding * 2
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA); panel.fill((0, 0, 0, 180))
        current_y = padding
        for line in rendered_lines:
            panel.blit(line, ((panel_width - line.get_width()) // 2, current_y)); current_y += line.get_height()
        surface.blit(panel, ((surface.get_width() - panel_width) // 2, (surface.get_height() - panel_height) // 2))

    # --- Startup: initial asset load, routing to the media-error screen ---
    while not refresh_assets():
        # Essential audio is missing. Show the error screen until the user
        # adds files and presses R (reload) or ESC (quit).
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        if not show_media_error_screen(screen, asset_paths, is_portable):
            return False

    # --- Main Loop ---
    running = True
    clock = pygame.time.Clock()

    def reload_or_error():
        """Handles [R]: stops audio, reloads assets, or routes to the media
        error screen when essential audio is missing. Returns True to keep the
        main loop running."""

        stop_all_sounds()
        if refresh_assets():
            return True

        # Essential audio is missing after a reload: keep waiting on the
        # media-error screen so the user can add files and press R again.
        if not show_media_error_screen(screen, asset_paths, is_portable):
            return False
        # User pressed R on the error screen -> try again.
        return reload_or_error()

    while running:
        current_bg_index = state["current_bg_index"]
        scaled_backgrounds = state["scaled_backgrounds"]
        current_display_image = state["current_display_image"]
        target_display_image = state["target_display_image"]
        fade_alpha = state["fade_alpha"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_SPACE: stop_all_sounds()
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT): show_text = not show_text
                elif event.key == pygame.K_r:
                    if not reload_or_error():
                        running = False
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
                current_bg_index = (state["current_bg_index"] + 1) % len(state["scaled_backgrounds"])
                state["current_bg_index"] = current_bg_index
                state["target_display_image"] = state["scaled_backgrounds"][current_bg_index]
                state["fade_alpha"] = 0

        # Drawing
        if target_display_image and fade_alpha < 255:
            fade_alpha = min(255, fade_alpha + 5)
            current_display_image.set_alpha(255 - fade_alpha); screen.blit(current_display_image, (0, 0))
            target_display_image.set_alpha(fade_alpha); screen.blit(target_display_image, (0, 0))
            if fade_alpha >= 255:
                state["current_display_image"] = target_display_image
                state["target_display_image"] = None
                state["fade_alpha"] = fade_alpha
        else:
            screen.blit(current_display_image, (0, 0))

        if show_text: draw_help_screen(screen)

        # Show a transient warning (e.g. >26 effects) if one is pending.
        pending_warning = state.get("effect_warning")
        if pending_warning:
            state["effect_warning"] = None
            root = tk.Tk(); root.withdraw()
            messagebox.showwarning("Auramixer - Effects Limit", pending_warning)
            root.destroy()

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

    run_main_program(screen, load_all_assets, asset_paths, IS_PORTABLE)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
