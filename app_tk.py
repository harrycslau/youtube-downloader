#!/usr/bin/env python3
"""
YouTube Downloader GUI App
A simple macOS app for downloading YouTube videos/audio using tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from pathlib import Path
from downloader import download_youtube


class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("550x380")
        self.root.resizable(False, False)
        
        # Default download path
        self.download_path = str(Path.home() / 'Downloads')
        
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
        
        # Download Button
        self.download_btn = ttk.Button(main_frame, text="⬇️ Download", command=self.start_download)
        self.download_btn.grid(row=7, column=0, columnspan=3, pady=(10, 10))
        
        # Status Label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="gray", wraplength=480)
        self.status_label.grid(row=8, column=0, columnspan=3, pady=(5, 5))
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=480)
        self.progress.grid(row=9, column=0, columnspan=3, pady=(10, 0))
    
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
            self.path_label.config(text=path)
    
    def start_download(self):
        """Start download in background thread"""
        url = self.url_entry.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        if 'youtube.com' not in url and 'youtu.be' not in url:
            messagebox.showerror("Error", "Please enter a valid YouTube URL")
            return
        
        # Disable button and start progress
        self.download_btn.config(state='disabled')
        self.progress.start(10)
        self.status_var.set("Starting download...")
        
        # Get quality value
        quality = self.quality_var.get()
        if "192kbps" in quality:
            quality = "best"
        elif "128kbps" in quality:
            quality = "worst"
        
        # Start download thread
        thread = threading.Thread(
            target=self._download_thread,
            args=(url, self.format_var.get(), quality),
            daemon=True
        )
        thread.start()
    
    def _download_thread(self, url, fmt, quality):
        """Background download thread"""
        def progress_callback(status, info):
            self.root.after(0, lambda: self.status_var.set(f"{status}: {info}"))
        
        result = download_youtube(
            url=url,
            download_type=fmt,
            quality=quality,
            output_path=self.download_path,
            progress_callback=progress_callback
        )
        
        # Update UI on main thread
        self.root.after(0, lambda: self._download_complete(result))
    
    def _download_complete(self, result):
        """Handle download completion"""
        self.progress.stop()
        self.download_btn.config(state='normal')
        
        if result['success']:
            self.status_var.set("✅ Download complete!")
            messagebox.showinfo("Success", f"Downloaded: {result['title']}\n\nSaved to: {self.download_path}")
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
