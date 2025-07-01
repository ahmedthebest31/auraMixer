# AuraMixer: Your Personal Soundscape Creator

Welcome to AuraMixer, a sleek and intuitive soundboard application designed to bring your audio and visual experiences to life. Built with Pygame, AuraMixer lets you effortlessly play custom music tracks and dynamic sound effects, all while enjoying stunning, smoothly transitioning background visuals. It's perfect for content creators, gamers, or anyone looking to add an immersive audio-visual layer to their desktop.

## What AuraMixer Offers

*   **Seamless Music Blending:**
    *   Load your favorite `.wav` or `.mp3` tunes from the `music/` folder.
    *   Assign tracks to numeric keys (1-0, including Numpad) for instant playback.
    *   Experience buttery-smooth transitions: when you switch tracks, the current song gracefully fades out as the new one fades in, ensuring your soundscape is never interrupted by jarring silence.
    *   All music tracks loop endlessly, creating a continuous ambient background.
*   **Expressive Sound Effects:**
    *   Populate the `effects/` folder with your preferred `.wav` or `.mp3` sound effects.
    *   Each alphabet key (A-Z) is uniquely mapped to a specific sound, allowing for consistent and precise triggering of your effects.
*   **Dynamic Visuals:**
    *   Drop your `.png`, `.jpg`, or `.jpeg` images into the `backgrounds/` folder.
    *   AuraMixer intelligently scales and crops images to perfectly fit your screen, just like CSS `background-size: cover`, so your visuals always look their best.
    *   Enjoy a captivating slideshow as background images smoothly fade into one another every 10 seconds.
*   **Full-Screen Immersion:**
    *   Dive into a distraction-free experience with a dedicated full-screen mode.
*   **Clean Interface:**
    *   Toggle the on-screen UI text with a simple press of the Shift key, keeping your display clutter-free when you want full immersion.
*   **Robust & User-Friendly:**
    *   AuraMixer gracefully handles missing or empty media folders, providing helpful messages without crashing.

## Getting Started (For Users - Executable Version)

If you've received AuraMixer as an executable file (e.g., `.exe` on Windows), simply:

1.  **Download and Unzip:** Get the AuraMixer executable package and extract its contents to a folder of your choice.
2.  **Prepare Your Media:**
    *   Inside the extracted AuraMixer folder, you'll find `music/`, `effects/`, and `backgrounds/` subfolders.
    *   Place your `.wav` or `.mp3` music files into the `music/` folder.
    *   Add your `.wav` or `.mp3` sound effects to the `effects/` folder.
    *   Put your `.png`, `.jpg`, or `.jpeg` background images into the `backgrounds/` folder.
3.  **Launch AuraMixer:** Double-click the `auramixer.exe` (or similar executable name) file to start the application.

## For Developers (Running from Source)

If you prefer to run AuraMixer directly from its Python source code:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/auramixer.git
    cd auramixer
    ```
    (Remember to replace `your-username` with your actual GitHub username if you fork this project.)

2.  **Install Pygame:**
    Ensure you have Python 3.x installed. Then, install the Pygame library:
    ```bash
    pip install pygame
    ```

3.  **Prepare Your Media:** (Same as step 2 for users above)

4.  **Run the Application:**
    Navigate to the project directory in your terminal and execute:
    ```bash
    python auramixer.py
    ```

## Keyboard Controls

*   **Numeric Keys (1-0, Numpad 1-0):** Play corresponding music tracks.
*   **Alphabet Keys (A-Z):** Trigger specific sound effects.
*   **Spacebar:** Smoothly fade out and stop all currently playing music and sound effects.
*   **Shift Key (Left or Right):** Toggle the visibility of the on-screen UI text.

## Project Structure

```
.
├── auramixer.py
├── music/
│   ├── your_track_name_1.mp3
│   └── your_track_name_2.wav
├── effects/
│   ├── your_sfx_name_1.wav
│   └── your_sfx_name_2.mp3
└── backgrounds/
    ├── your_image_1.png
    └── your_image_2.jpg
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. (Note: You might need to create a `LICENSE` file if you want to specify a license.)
