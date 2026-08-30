# AuraMixer ✨

*Your personal real-time audio and visual mixer for creating immersive ambiances.*


<img src="assets/icon.png" alt="auraMixer icon" width="450" />

AuraMixer is a versatile application for Windows, macOS, and Linux that transforms your desktop into a dynamic sensory experience. Mix ambient background music, trigger sound effects on the fly, and enjoy a slideshow of your favorite visuals, all controlled seamlessly from your keyboard.

---

## 🌟 Features

*   🎵 **Dynamic Audio Mixing**: Effortlessly play and crossfade between multiple background music tracks for smooth transitions.
*   🔊 **Instant Sound Effects**: Trigger a library of sound effects instantly using your keyboard's alphabet keys.
*   🖼️ **Visual Ambiance**: Enjoy a beautiful, fullscreen slideshow of your personal images that automatically crossfade.
*   🎹 **Intuitive Keyboard Control**: A powerful, keyboard-first interface allows you to control everything without ever touching your mouse.
*   🎚️ **Granular Volume Control**: Independently adjust the volume for background music and sound effects to get the perfect mix.
*   🔄 **Live Asset Reload**: Add new music, effects, or images and reload them instantly with a single key press—no restart required!
*   📦 **Cross-Platform**: Standalone executables for Windows, macOS, and Linux.

---

## 🚀 Installation & Setup

Getting started with AuraMixer is easy. No installation is required!

1.  **Download:** Grab the latest version for your operating system (Windows, macOS, or Linux) from the **[Releases page](https://github.com/ahmedthebest31/auraMixer/releases)**.
2.  **Unzip:** Extract the contents of the downloaded `.zip` file to a folder of your choice.
3.  **Add Your Media:** Inside the extracted folder, you will find three subfolders:
    *   `music/`: Place your background music files (e.g., `.mp3`, `.wav`) here.
    *   `effects/`: Place your sound effect files (e.g., `.mp3`, `.wav`) here.
    *   `backgrounds/`: Place your background image files (e.g., `.png`, `.jpg`) here.
4.  **Launch:** Double-click the `auramixer` executable file to start the application.

---

## ⌨️ How to Use (Controls)

AuraMixer is controlled entirely via your keyboard.

| Key(s)              | Action                                               |
| ------------------- | ---------------------------------------------------- |
| **Alphabet (A-Z)**  | Play a corresponding sound effect from the `effects` folder. |
| **Numbers (1-0)**   | Play a corresponding music track from the `music` folder. |
| **Numpad (1-0)**    | Also plays a corresponding music track.              |
| **Spacebar**        | Fade out and stop all currently playing audio.       |
| **Arrow Up/Down**   | Increase/Decrease the volume of the background music. |
| **Arrow Left/Right**| Increase/Decrease the volume of the sound effects.   |
| **Shift (L or R)**  | Toggle the on-screen help text and volume display.   |
| **R**               | Reload all music, effects, and backgrounds from the folders. |
| **ESC**             | Quit the application.                                |

---

## 🛠️ Development

AuraMixer is a single-file Python application built with [Pygame - Community Edition](https://pypi.org/project/pygame-ce/) (the actively maintained fork that supports recent Python versions).

1.  **Environment:** Python 3.10+ (recommended: latest stable, e.g. 3.14).
2.  **Setup:** From the project root run `uv sync` (or `pip install -r requirements.txt`).
3.  **Run:** `python auramixer.py`
4.  **Test:** `python -m unittest test_auramixer -v`
5.  **Build:** `pyinstaller auramixer.spec`

---

## 🤝 Contributing

Contributions to this project are welcome! If you find a bug, have an idea for an improvement, or want to contribute in any other way, please feel free to open an issue or submit a pull request.


---

## 📝 License

This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for more details.