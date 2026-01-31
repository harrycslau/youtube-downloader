"""
YouTube Downloader Module
Provides download functionality for YouTube videos/audio using yt-dlp
"""

import yt_dlp
import os
from pathlib import Path


def download_youtube(url, download_type='mp4', quality='best', output_path=None, progress_callback=None):
    """
    Download YouTube videos as MP4 or MP3/M4A
    
    Args:
        url (str): YouTube URL
        download_type (str): 'mp4' for video, 'mp3' for audio MP3, 'm4a' for audio M4A
        quality (str): Quality options:
            - For MP4: 'best', 'worst', '720p', '480p', '360p', '1080p'
            - For MP3/M4A: 'best', 'worst' (audio quality)
        output_path (str): Directory to save downloads (defaults to ~/Downloads)
        progress_callback (callable): Optional callback for progress updates
    
    Returns:
        dict: Result with 'success' (bool), 'title' (str), 'message' (str)
    """
    
    # Default to ~/Downloads if no path specified
    if output_path is None:
        output_path = str(Path.home() / 'Downloads')
    
    # Create output directory if it doesn't exist
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    def progress_hook(d):
        if progress_callback:
            if d['status'] == 'downloading':
                progress_callback('downloading', d.get('_percent_str', '0%'))
            elif d['status'] == 'finished':
                progress_callback('finished', '100%')
    
    if download_type == 'mp4':
        # Video download options
        if quality == 'best':
            format_selector = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == 'worst':
            format_selector = 'worst[ext=mp4]'
        elif quality in ['720p', '480p', '360p', '1080p']:
            height = quality.replace('p', '')
            format_selector = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best[ext=mp4]'
        else:
            format_selector = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
        ydl_opts = {
            'format': format_selector,
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',
        }
        
    elif download_type == 'mp3':
        # Audio download options for MP3
        audio_quality = '192' if quality == 'best' else '128'
        ydl_opts = {
            'format': 'bestaudio/best' if quality == 'best' else 'worstaudio/worst',
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_quality,
            }],
        }
    elif download_type == 'm4a':
        # Audio download options for M4A
        audio_quality = '192' if quality == 'best' else '128'
        ydl_opts = {
            'format': 'bestaudio/best' if quality == 'best' else 'worstaudio/worst',
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': audio_quality,
            }],
        }
    else:
        return {
            'success': False,
            'title': None,
            'message': "Invalid download_type. Use 'mp4', 'mp3', or 'm4a'."
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            if progress_callback:
                progress_callback('info', f"{title} ({duration//60}:{duration%60:02d})")
            
            # Download the video/audio
            ydl.download([url])
            
            return {
                'success': True,
                'title': title,
                'message': f"Downloaded: {title}"
            }
            
    except Exception as e:
        error_msg = str(e)
        if "Private video" in error_msg:
            error_msg = "Video is private or restricted"
        elif "Video unavailable" in error_msg:
            error_msg = "Video is unavailable"
        elif "urlopen error" in error_msg.lower():
            error_msg = "Network connection issue"
            
        return {
            'success': False,
            'title': None,
            'message': f"Error: {error_msg}"
        }


def get_video_info(url):
    """
    Get video information without downloading
    
    Args:
        url (str): YouTube URL
    
    Returns:
        dict: Video info with 'success', 'title', 'duration', 'message'
    """
    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'success': True,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'message': 'OK'
            }
    except Exception as e:
        return {
            'success': False,
            'title': None,
            'duration': 0,
            'message': str(e)
        }
