
import pygame
import os
import random
import sys
import atexit

# --- Single Instance Check ---
LOCK_FILE = os.path.join(os.path.expanduser("~"), "auramixer.lock")

if os.path.exists(LOCK_FILE):
    print("Another instance of Auramixer is already running.")
    sys.exit(1)

def cleanup_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))
atexit.register(cleanup_lock_file)


# Initialize Pygame
pygame.init()
pygame.mixer.init()
pygame.display.set_caption("Auramixer")

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FONT_COLOR = (255, 255, 0) # Yellow for visibility

# Create the screen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
font = pygame.font.Font(None, 36)

# UI text visibility
show_text = False

# --- Asset Loading ---
def get_absolute_path(relative_path):
    """Get the absolute path to a resource, accommodating PyInstaller's temporary folder."""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app 
        # path into variable _MEIPASS'.
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(application_path, relative_path)

def scale_and_crop_image(original_image):
    img_aspect = original_image.get_width() / original_image.get_height()
    screen_aspect = SCREEN_WIDTH / SCREEN_HEIGHT
    if img_aspect > screen_aspect:
        new_height = SCREEN_HEIGHT
        new_width = int(new_height * img_aspect)
    else:
        new_width = SCREEN_WIDTH
        new_height = int(new_width / img_aspect)
    scaled_image = pygame.transform.scale(original_image, (new_width, new_height))
    x_offset = (new_width - SCREEN_WIDTH) // 2
    y_offset = (new_height - SCREEN_HEIGHT) // 2
    cropped_image = scaled_image.subsurface(pygame.Rect(x_offset, y_offset, SCREEN_WIDTH, SCREEN_HEIGHT))
    return cropped_image

# Load background images
def load_background_images():
    global all_background_images, current_display_image, target_display_image, fade_alpha, BACKGROUND_CHANGE_EVENT, current_bg_index
    background_folder = get_absolute_path("backgrounds")
    all_background_images = []
    if os.path.exists(background_folder):
        for f in os.listdir(background_folder):
            if f.endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(background_folder, f)
                original_image = pygame.image.load(img_path).convert()
                all_background_images.append(scale_and_crop_image(original_image))

    if all_background_images:
        current_bg_index = 0
        current_display_image = all_background_images[current_bg_index]
        target_display_image = None
        fade_alpha = 255
        BACKGROUND_CHANGE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(BACKGROUND_CHANGE_EVENT, 10000) # Change every 10 seconds
    else:
        current_display_image = None
        target_display_image = None
        print("No background images found in 'backgrounds' folder.")

load_background_images()

# Load scream sounds
def load_scream_sounds():
    global scream_sounds, scream_map
    scream_folder = get_absolute_path("effects")
    scream_sounds = []
    if os.path.exists(scream_folder):
        scream_sounds = [pygame.mixer.Sound(os.path.join(scream_folder, f)) for f in os.listdir(scream_folder) if f.endswith(('.wav', '.mp3'))]
    if not scream_sounds:
        print("No effects sounds found in 'effects' folder.")

    # Map alphabet keys to scream sounds
    scream_map = {}
    if scream_sounds:
        for i, key_code in enumerate(range(pygame.K_a, pygame.K_z + 1)):
            if i < len(scream_sounds):
                scream_map[key_code] = scream_sounds[i]

def load_music_tracks():
    global music_files
    music_folder = get_absolute_path("music")
    music_files = []
    if os.path.exists(music_folder):
        for f in os.listdir(music_folder):
            if f.endswith(('.wav', '.mp3')):
                try:
                    music_files.append(pygame.mixer.Sound(os.path.join(music_folder, f)))
                except pygame.error as e:
                    print(f"Could not load music file {f}: {e}")
    if not music_files:
        print("No music tracks found in 'music' folder.")

load_scream_sounds()
load_music_tracks()

# --- Sound Playback ---
channel1 = pygame.mixer.Channel(0)
channel2 = pygame.mixer.Channel(1)
current_channel = channel1
fading_channel = channel2

# Volume settings
music_volume = 0.5 # Initial music volume (0.0 to 1.0)
scream_volume = 0.7 # Initial scream volume (0.0 to 1.0)

def play_scream(key_code):
    global scream_volume
    if key_code in scream_map:
        scream_map[key_code].set_volume(scream_volume)
        scream_map[key_code].play()

def play_music(track_index):
    global current_channel, fading_channel, music_volume
    if 0 <= track_index < len(music_files):
        # Start fading out the current music
        if current_channel.get_busy():
            current_channel.fadeout(2000) # Fade out over 2 seconds

        # Load and play the new music on the other channel, fading in
        fading_channel.set_volume(music_volume)
        fading_channel.play(music_files[track_index], loops=-1, fade_ms=2000)

        # Swap channels
        current_channel, fading_channel = fading_channel, current_channel

def stop_all_sounds():
    current_channel.fadeout(2000)
    fading_channel.fadeout(2000)
    # No pygame.mixer.stop() here to allow fadeout to complete


# --- Main Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == BACKGROUND_CHANGE_EVENT:
            if len(all_background_images) > 1: # Only change if there's more than one image
                current_bg_index = (current_bg_index + 1) % len(all_background_images)
                target_display_image = all_background_images[current_bg_index]
                fade_alpha = 0
        if event.type == pygame.KEYDOWN:
            if event.key >= pygame.K_a and event.key <= pygame.K_z:
                play_scream(event.key)
            elif event.key == pygame.K_SPACE:
                stop_all_sounds()
            elif event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
                show_text = not show_text
            elif event.key == pygame.K_r: # R key to reload assets
                load_background_images()
                load_scream_sounds()
                load_music_tracks()
            elif event.key == pygame.K_UP:
                music_volume = min(1.0, music_volume + 0.1)
                current_channel.set_volume(music_volume)
                fading_channel.set_volume(music_volume)
            elif event.key == pygame.K_DOWN:
                music_volume = max(0.0, music_volume - 0.1)
                current_channel.set_volume(music_volume)
                fading_channel.set_volume(music_volume)
            elif event.key == pygame.K_LEFT:
                scream_volume = max(0.0, scream_volume - 0.1)
            elif event.key == pygame.K_RIGHT:
                scream_volume = min(1.0, scream_volume + 0.1)
            # Music key mappings (Top row and Numpad)
            # Check top row numbers 1-9 and 0
            elif pygame.K_1 <= event.key <= pygame.K_9:
                play_music(event.key - pygame.K_1)
            elif event.key == pygame.K_0:
                 play_music(9) # Map '0' to the 10th track
            # Check Numpad numbers 1-9 and 0
            elif pygame.K_KP1 <= event.key <= pygame.K_KP9:
                play_music(event.key - pygame.K_KP1)
            elif event.key == pygame.K_KP0:
                play_music(9) # Map 'KP0' to the 10th track

    # --- Drawing ---
    if current_display_image:
        if target_display_image and fade_alpha < 255:
            fade_alpha += 5 # Adjust fade speed here
            if fade_alpha > 255:
                fade_alpha = 255
            
            # Draw the current background image (fading out)
            temp_surface_current = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            temp_surface_current.blit(current_display_image, (0, 0))
            temp_surface_current.set_alpha(255 - fade_alpha) # Fade out
            screen.blit(temp_surface_current, (0, 0))

            # Draw the next background image (fading in)
            temp_surface_next = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            temp_surface_next.blit(target_display_image, (0, 0))
            temp_surface_next.set_alpha(fade_alpha) # Fade in
            screen.blit(temp_surface_next, (0, 0))

            if fade_alpha == 255:
                current_display_image = target_display_image
                target_display_image = None
        else:
            screen.blit(current_display_image, (0, 0))
    else:
        screen.fill(BLACK)

    # Display key mappings
    if show_text:
        info_text = [
            "Alphabet Keys: Play Specific Scream",
            "Space: Stop All Sounds",
            "Shift: Toggle UI Text",
            f"Music Volume: {music_volume:.1f}",
            f"Effects Volume: {scream_volume:.1f}",
            "--------------------"
        ]
        for i, f in enumerate(music_files):
            if i < 10: # Support up to 10 tracks for number keys 1-0
                key = i + 1 if i < 9 else 0
                track_name = os.path.splitext(os.path.basename(f))[0]
                info_text.append(f"Num {key}: {track_name}")

        for i, line in enumerate(info_text):
            text_surface = font.render(line, True, FONT_COLOR)
            screen.blit(text_surface, (10, 10 + i * 40))


    pygame.display.flip()

pygame.quit()
sys.exit()
