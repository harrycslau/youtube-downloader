#!/usr/bin/env python3
"""
YouTube Downloader Menu Bar App
A lightweight macOS menu bar app for downloading YouTube videos/audio
"""

import rumps
import threading
from pathlib import Path
from downloader import download_youtube, get_video_info


class YouTubeDownloaderApp(rumps.App):
    def __init__(self):
        super(YouTubeDownloaderApp, self).__init__(
            "YT",
            icon=None,  # Uses text "YT" as icon
            quit_button=None  # We'll add a custom quit button
        )
        
        # Settings
        self.download_path = str(Path.home() / 'Downloads')
        self.current_format = 'mp4'
        self.current_quality = 'best'
        
        # Build menu
        self.menu = [
            rumps.MenuItem('📥 Download Video...', callback=self.download_video),
            None,  # Separator
            self._build_format_menu(),
            self._build_quality_menu(),
            None,  # Separator
            rumps.MenuItem(f'📁 Save to: ~/Downloads', callback=self.change_download_path),
            None,  # Separator
            rumps.MenuItem('Quit', callback=self.quit_app),
        ]
    
    def _build_format_menu(self):
        """Build the format selection submenu"""
        format_menu = rumps.MenuItem('Format')
        
        formats = [
            ('MP4 (Video)', 'mp4'),
            ('MP3 (Audio)', 'mp3'),
            ('M4A (Audio)', 'm4a'),
        ]
        
        for label, fmt in formats:
            item = rumps.MenuItem(label, callback=self._make_format_callback(fmt))
            if fmt == self.current_format:
                item.state = 1  # Checkmark
            format_menu.add(item)
        
        return format_menu
    
    def _build_quality_menu(self):
        """Build the quality selection submenu"""
        quality_menu = rumps.MenuItem('Quality')
        
        qualities = [
            ('Best', 'best'),
            ('1080p', '1080p'),
            ('720p', '720p'),
            ('480p', '480p'),
            ('360p', '360p'),
            None,  # Separator
            ('Audio: High (192kbps)', 'best'),
            ('Audio: Low (128kbps)', 'worst'),
        ]
        
        for item in qualities:
            if item is None:
                quality_menu.add(None)
            else:
                label, qual = item
                menu_item = rumps.MenuItem(label, callback=self._make_quality_callback(qual))
                if qual == self.current_quality:
                    menu_item.state = 1
                quality_menu.add(menu_item)
        
        return quality_menu
    
    def _make_format_callback(self, fmt):
        """Create a callback for format selection"""
        def callback(sender):
            self.current_format = fmt
            # Update checkmarks
            for item in self.menu['Format'].values():
                if hasattr(item, 'state'):
                    item.state = 0
            sender.state = 1
            rumps.notification(
                title="Format Changed",
                subtitle="",
                message=f"Download format set to {fmt.upper()}"
            )
        return callback
    
    def _make_quality_callback(self, qual):
        """Create a callback for quality selection"""
        def callback(sender):
            self.current_quality = qual
            # Update checkmarks in quality menu
            for item in self.menu['Quality'].values():
                if hasattr(item, 'state'):
                    item.state = 0
            sender.state = 1
            quality_name = qual if qual in ['best', 'worst'] else qual
            rumps.notification(
                title="Quality Changed",
                subtitle="",
                message=f"Download quality set to {quality_name}"
            )
        return callback
    
    def download_video(self, _):
        """Show dialog to enter YouTube URL and start download"""
        window = rumps.Window(
            message='Paste YouTube URL:',
            title='YouTube Downloader',
            default_text='',
            ok='Download',
            cancel='Cancel',
            dimensions=(400, 24)
        )
        
        response = window.run()
        
        if response.clicked and response.text.strip():
            url = response.text.strip()
            
            # Validate URL
            if 'youtube.com' not in url and 'youtu.be' not in url:
                rumps.notification(
                    title="Invalid URL",
                    subtitle="",
                    message="Please enter a valid YouTube URL"
                )
                return
            
            # Start download in background thread
            thread = threading.Thread(
                target=self._download_thread,
                args=(url,),
                daemon=True
            )
            thread.start()
            
            rumps.notification(
                title="Download Started",
                subtitle=f"Format: {self.current_format.upper()} | Quality: {self.current_quality}",
                message="Fetching video info..."
            )
    
    def _download_thread(self, url):
        """Background thread for downloading"""
        def progress_callback(status, info):
            if status == 'info':
                rumps.notification(
                    title="Downloading...",
                    subtitle="",
                    message=info
                )
        
        result = download_youtube(
            url=url,
            download_type=self.current_format,
            quality=self.current_quality,
            output_path=self.download_path,
            progress_callback=progress_callback
        )
        
        if result['success']:
            rumps.notification(
                title="✅ Download Complete!",
                subtitle=result['title'] or "",
                message=f"Saved to {self.download_path}"
            )
        else:
            rumps.notification(
                title="❌ Download Failed",
                subtitle="",
                message=result['message']
            )
    
    def change_download_path(self, sender):
        """Show info about download path (rumps doesn't support folder picker)"""
        rumps.notification(
            title="Download Location",
            subtitle="",
            message=f"Files are saved to: {self.download_path}"
        )
    
    def quit_app(self, _):
        """Quit the application"""
        rumps.quit_application()


if __name__ == "__main__":
    YouTubeDownloaderApp().run()
