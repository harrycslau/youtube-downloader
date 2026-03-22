#!/usr/bin/env python3
"""
YouTube Downloader GUI App
A simple macOS app for downloading YouTube videos/audio using tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from pathlib import Path
import shutil
from downloader import download_youtube


class YouTubeDownloaderApp:
    CONFIG_PATH = Path.home() / '.youtube_downloader_config.json'
    COMMON_FFMPEG_DIRS = [
        Path('/opt/homebrew/bin'),
        Path('/usr/local/bin'),
        Path.home() / 'homebrew' / 'bin',
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("620x470")
        self.root.resizable(False, False)
        
        # Default download path
        self.download_path = str(Path.home() / 'Downloads')
        self.download_path_confirmed = False
        self.ffmpeg_location = None
        self._load_config()
        
        # Create main frame with padding
        main_frame = ttk.Frame(root, padding="25")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL Entry
        ttk.Label(main_frame, text="YouTube URL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.url_entry = ttk.Entry(main_frame, width=55)
        self.url_entry.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Format Selection
        ttk.Label(main_frame, text="Format:").grid(row=2, column=0, sticky=tk.W)
        self.format_var = tk.StringVar(value="mp4")
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 15))
        
        ttk.Radiobutton(format_frame, text="MP4 (Video)", variable=self.format_var, 
                       value="mp4", command=self.update_quality_options).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(format_frame, text="MP3 (Audio)", variable=self.format_var, 
                       value="mp3", command=self.update_quality_options).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(format_frame, text="M4A (Audio)", variable=self.format_var, 
                       value="m4a", command=self.update_quality_options).pack(side=tk.LEFT)
        
        # Quality Selection
        ttk.Label(main_frame, text="Quality:").grid(row=4, column=0, sticky=tk.W)
        self.quality_var = tk.StringVar(value="best")
        self.quality_combo = ttk.Combobox(main_frame, textvariable=self.quality_var, state="readonly", width=20)
        self.quality_combo.grid(row=5, column=0, sticky=tk.W, pady=(0, 15))
        self.update_quality_options()
        
        # Download Path
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(path_frame, text="Save to:").pack(side=tk.LEFT)
        self.path_label = ttk.Label(path_frame, text=self.download_path, foreground="gray")
        self.path_label.pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(path_frame, text="Change...", command=self.change_path).pack(side=tk.LEFT)

        # FFmpeg setup
        ffmpeg_frame = ttk.LabelFrame(main_frame, text="FFmpeg Setup", padding="12")
        ffmpeg_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        ffmpeg_frame.columnconfigure(1, weight=1)

        ttk.Label(ffmpeg_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        self.ffmpeg_status_var = tk.StringVar()
        self.ffmpeg_status_label = ttk.Label(
            ffmpeg_frame,
            textvariable=self.ffmpeg_status_var,
            foreground="gray",
            wraplength=420
        )
        self.ffmpeg_status_label.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E))

        ttk.Button(ffmpeg_frame, text="Choose ffmpeg...", command=self.choose_ffmpeg).grid(
            row=1, column=0, sticky=tk.W, pady=(10, 0)
        )
        ttk.Button(ffmpeg_frame, text="Auto-detect", command=self.auto_detect_ffmpeg).grid(
            row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(8, 0)
        )
        ttk.Button(ffmpeg_frame, text="Install Help", command=self.show_ffmpeg_help).grid(
            row=1, column=2, sticky=tk.E, pady=(10, 0)
        )
        
        # Download Button
        self.download_btn = ttk.Button(main_frame, text="⬇️ Download", command=self.start_download)
        self.download_btn.grid(row=8, column=0, columnspan=3, pady=(10, 10))
        
        # Status Label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="gray", wraplength=480)
        self.status_label.grid(row=9, column=0, columnspan=3, pady=(5, 5))
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=480)
        self.progress.grid(row=10, column=0, columnspan=3, pady=(10, 0))

        self.refresh_ffmpeg_status()

    def _load_config(self):
        """Load persisted app settings."""
        if not self.CONFIG_PATH.exists():
            return

        try:
            config = json.loads(self.CONFIG_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return

        self.download_path = config.get('download_path', self.download_path)
        self.download_path_confirmed = config.get('download_path_confirmed', False)
        self.ffmpeg_location = config.get('ffmpeg_location') or None

    def _save_config(self):
        """Persist app settings."""
        config = {
            'download_path': self.download_path,
            'download_path_confirmed': self.download_path_confirmed,
            'ffmpeg_location': self.ffmpeg_location,
        }
        self.CONFIG_PATH.write_text(json.dumps(config, indent=2))

    def _resolve_ffmpeg(self):
        """Return the usable ffmpeg executable path if available."""
        configured = self.ffmpeg_location
        if configured:
            path = Path(configured).expanduser()
            if path.is_dir():
                candidate = path / 'ffmpeg'
            else:
                candidate = path
            if candidate.exists():
                return str(candidate)

        detected = shutil.which('ffmpeg')
        if detected:
            return detected

        for directory in self.COMMON_FFMPEG_DIRS:
            candidate = directory / 'ffmpeg'
            if candidate.exists():
                return str(candidate)

        return None

    def refresh_ffmpeg_status(self):
        """Update visible FFmpeg status text."""
        ffmpeg_path = self._resolve_ffmpeg()
        if ffmpeg_path:
            self.ffmpeg_status_var.set(
                f"Ready for audio downloads: {ffmpeg_path}"
            )
        else:
            self.ffmpeg_status_var.set(
                "Audio downloads need FFmpeg. Click 'Choose ffmpeg...' or install it with 'brew install ffmpeg'."
            )
    
    def update_quality_options(self):
        """Update quality dropdown based on selected format"""
        fmt = self.format_var.get()
        if fmt == "mp4":
            options = ["best", "1080p", "720p", "480p", "360p"]
        else:
            options = ["best (192kbps)", "low (128kbps)"]
        
        self.quality_combo['values'] = options
        self.quality_var.set(options[0])
    
    def change_path(self):
        """Open folder picker dialog"""
        path = filedialog.askdirectory(initialdir=self.download_path)
        if path:
            self.download_path = path
            self.download_path_confirmed = True
            self.path_label.config(text=path)
            self._save_config()

    def ensure_download_path_access(self):
        """Require explicit folder selection for protected macOS folders like Downloads."""
        downloads_path = str(Path.home() / 'Downloads')
        if self.download_path != downloads_path or self.download_path_confirmed:
            return True

        messagebox.showinfo(
            "Confirm Downloads Folder",
            "macOS may not grant reliable access to Downloads unless you choose it explicitly.\n\n"
            "Click OK, then re-select your Downloads folder in the picker."
        )

        path = filedialog.askdirectory(initialdir=self.download_path)
        if not path:
            self.status_var.set("Download cancelled: folder access not confirmed")
            return False

        self.download_path = path
        self.download_path_confirmed = True
        self.path_label.config(text=path)
        self._save_config()
        return True

    def choose_ffmpeg(self):
        """Pick the ffmpeg executable."""
        initial_dir = str(Path(self.ffmpeg_location).expanduser().parent) if self.ffmpeg_location else str(Path.home())
        selected = filedialog.askopenfilename(
            title="Choose ffmpeg executable",
            initialdir=initial_dir,
        )
        if not selected:
            return

        candidate = Path(selected).expanduser()
        if candidate.name != 'ffmpeg':
            messagebox.showerror(
                "Invalid Selection",
                "Please choose the ffmpeg executable itself, not another file."
            )
            return

        self.ffmpeg_location = str(candidate)
        self._save_config()
        self.refresh_ffmpeg_status()

    def auto_detect_ffmpeg(self):
        """Store an auto-detected FFmpeg path when available."""
        ffmpeg_path = self._resolve_ffmpeg()
        if not ffmpeg_path:
            self.refresh_ffmpeg_status()
            self.show_ffmpeg_help()
            return

        self.ffmpeg_location = ffmpeg_path
        self._save_config()
        self.refresh_ffmpeg_status()
        messagebox.showinfo("FFmpeg Detected", f"Using FFmpeg at:\n\n{ffmpeg_path}")

    def show_ffmpeg_help(self):
        """Explain how to install or configure FFmpeg."""
        messagebox.showinfo(
            "FFmpeg Required for Audio",
            "MP3 and M4A downloads need FFmpeg.\n\n"
            "Fastest fix on macOS:\n"
            "1. Install Homebrew if needed\n"
            "2. Run: brew install ffmpeg\n"
            "3. Click 'Auto-detect' here\n\n"
            "If FFmpeg is already installed but the app cannot see it, click 'Choose ffmpeg...' and select the ffmpeg binary."
        )
    
    def start_download(self):
        """Start download in background thread"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        if 'youtube.com' not in url and 'youtu.be' not in url:
            messagebox.showerror("Error", "Please enter a valid YouTube URL")
            return

        if not self.ensure_download_path_access():
            return
        
        # Get quality value
        quality = self.quality_var.get()
        if "192kbps" in quality:
            quality = "best"
        elif "128kbps" in quality:
            quality = "worst"

        ffmpeg_path = self._resolve_ffmpeg()
        if self.format_var.get() in {'mp3', 'm4a'} and not ffmpeg_path:
            self.show_ffmpeg_help()
            self.status_var.set("Audio download blocked: FFmpeg setup required")
            return

        # Disable button and start progress
        self.download_btn.config(state='disabled')
        self.progress.start(10)
        self.status_var.set("Starting download...")
        
        # Start download thread
        thread = threading.Thread(
            target=self._download_thread,
            args=(url, self.format_var.get(), quality, ffmpeg_path),
            daemon=True
        )
        thread.start()
    
    def _download_thread(self, url, fmt, quality, ffmpeg_path):
        """Background download thread"""
        def progress_callback(status, info):
            self.root.after(0, lambda: self.status_var.set(f"{status}: {info}"))
        
        result = download_youtube(
            url=url,
            download_type=fmt,
            quality=quality,
            output_path=self.download_path,
            progress_callback=progress_callback,
            ffmpeg_location=ffmpeg_path
        )
        
        # Update UI on main thread
        self.root.after(0, lambda: self._download_complete(result))
    
    def _download_complete(self, result):
        """Handle download completion"""
        self.progress.stop()
        self.download_btn.config(state='normal')
        
        if result['success']:
            saved_path = result.get('filepath') or self.download_path
            self.status_var.set(f"✅ Saved: {Path(saved_path).name}")
            messagebox.showinfo("Success", f"Downloaded: {result['title']}\n\nSaved as:\n{saved_path}")
        else:
            self.status_var.set("❌ Download failed")
            messagebox.showerror("Error", result['message'])


def main():
    root = tk.Tk()
    
    # Set app icon/title for macOS
    root.title("YouTube Downloader")
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')
    
    app = YouTubeDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
