# YouTube Downloader

A simple macOS application for downloading YouTube videos and audio with a user-friendly GUI.

## Features

- 🎥 **Video Download**: Download YouTube videos in MP4 format
- 🎵 **Audio Download**: Extract audio as MP3 or M4A
- 🎯 **Quality Selection**: Choose from multiple quality options
  - Video: Best, 1080p, 720p, 480p, 360p
  - Audio: High (192kbps) or Low (128kbps)
- 📁 **Custom Save Location**: Choose where to save your downloads (defaults to ~/Downloads)
- ✨ **Simple GUI**: Clean, easy-to-use interface built with tkinter
- 📦 **Standalone App**: Packaged as a macOS .app bundle

## Prerequisites

- macOS (tested on macOS 15.5)
- **ffmpeg** (required for audio extraction/conversion)

Install ffmpeg via Homebrew:
```bash
brew install ffmpeg
```

## Installation

### Option 1: Use the Pre-built App

1. Download `YouTube Downloader.app` from the `dist` folder
2. Drag it to your Applications folder
3. Right-click and select **Open** (first time only, to bypass Gatekeeper)

### Option 2: Run from Source

1. Clone the repository:
```bash
git clone <repository-url>
cd youtube-downloader
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # or: .venv/bin/activate on some systems
```

3. Install dependencies:
```bash
pip install yt-dlp
```

4. Run the app:
```bash
python app_tk.py
```

## Usage

1. Launch the **YouTube Downloader** app
2. Paste a YouTube URL into the text field
3. Select your desired format:
   - **MP4 (Video)** - Full video with audio
   - **MP3 (Audio)** - Audio only in MP3 format
   - **M4A (Audio)** - Audio only in M4A format
4. Choose quality from the dropdown
5. If you want MP3 or M4A, check the **FFmpeg Setup** section:
   - Click **Auto-detect** if ffmpeg is already installed
   - Or click **Choose ffmpeg...** and select the `ffmpeg` binary manually
6. If you save to **Downloads** on macOS, click **Change...** once and re-select the Downloads folder so the app gets explicit access
7. Click **⬇️ Download** and wait for completion

## Project Structure

```
youtube-downloader/
├── app_tk.py           # Main GUI application (tkinter)
├── downloader.py       # Core download logic using yt-dlp
├── main.ipynb          # Original Jupyter notebook
├── dist/               # Packaged .app bundle
├── downloads/          # Default download directory
└── README.md          # This file
```

## Building from Source

To rebuild the macOS app bundle:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the app bundle from the macOS spec
pyinstaller "YouTube Downloader.spec"
```

The built app will be in the `dist` folder as `dist/YouTube Downloader.app`.

This project uses PyInstaller `--onedir` instead of `--onefile` because it launches much faster on macOS.
The spec also includes the macOS Downloads-folder usage description so the app can request access to `~/Downloads`.

## Technical Details

- **GUI Framework**: tkinter (built-in Python library)
- **Download Engine**: [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Audio Processing**: FFmpeg
- **Packaging**: PyInstaller
- **Python Version**: 3.12+

## Troubleshooting

### App won't open
- Right-click the app and select **Open** (instead of double-clicking)
- macOS may show a security warning on first launch

### Audio formats not working
- Ensure ffmpeg is installed: `brew install ffmpeg`
- Verify installation: `ffmpeg -version`
- In the app, use the **FFmpeg Setup** section to auto-detect or manually choose the `ffmpeg` executable

### Saving to Downloads fails or files disappear
- Rebuild using `pyinstaller "YouTube Downloader.spec"` so the app bundle includes the macOS Downloads access metadata
- Launch the rebuilt app and allow access if macOS prompts for the Downloads folder
- In the app, click **Change...** and re-select the Downloads folder once so macOS grants explicit access to that folder

### Download fails
- Check that the YouTube URL is valid and accessible
- Some videos may be region-locked or age-restricted
- Ensure you have a stable internet connection

## License

This project is for personal use only. Please respect YouTube's Terms of Service.

## Contributing

Feel free to submit issues or pull requests for improvements!
