"""
YouTube Downloader Module
Provides download functionality for YouTube videos/audio using yt-dlp
"""

import yt_dlp
from pathlib import Path


def _normalize_result_info(info):
    """Return a single downloaded item from yt-dlp's result structure."""
    if not info:
        return info
    if 'entries' in info:
        entries = [entry for entry in info.get('entries', []) if entry]
        if entries:
            return entries[0]
    return info

def download_youtube(
    url,
    download_type='mp4',
    quality='best',
    output_path=None,
    progress_callback=None,
    ffmpeg_location=None,
):
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
        ffmpeg_location (str): Optional path to ffmpeg binary or containing folder
    
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
                progress_callback('downloaded', 'Download finished')

    def postprocessor_hook(d):
        if not progress_callback:
            return

        status = d.get('status')
        postprocessor = d.get('postprocessor', 'Post-processing')
        if status == 'started':
            progress_callback('processing', f"{postprocessor}...")
        elif status == 'finished':
            progress_callback('processing', f"{postprocessor} done")
    
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
            'postprocessor_hooks': [postprocessor_hook],
            'merge_output_format': 'mp4',
        }
        
    elif download_type == 'mp3':
        # Audio download options for MP3
        audio_quality = '192' if quality == 'best' else '128'
        ydl_opts = {
            'format': 'bestaudio/best' if quality == 'best' else 'worstaudio/worst',
            'outtmpl': f'{output_path}/%(title)s.%(ext)s',
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [postprocessor_hook],
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
            'postprocessor_hooks': [postprocessor_hook],
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

    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Fetch metadata and perform the download in one pass so we can use yt-dlp's final filepath.
            info = ydl.extract_info(url, download=True)
            info = _normalize_result_info(info)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            if progress_callback:
                progress_callback('info', f"{title} ({duration//60}:{duration%60:02d})")
 
            final_path = info.get('filepath')
            if not final_path:
                requested_downloads = info.get('requested_downloads') or []
                if requested_downloads:
                    final_path = requested_downloads[0].get('filepath')

            if not final_path:
                final_path = ydl.prepare_filename(info)

            final_path = Path(final_path)
            if not final_path.exists():
                raise FileNotFoundError(
                    f"Download completed but the final file was not found at {final_path}"
                )
            
            return {
                'success': True,
                'title': title,
                'filepath': str(final_path),
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
        elif "ffprobe and ffmpeg not found" in error_msg.lower():
            error_msg = (
                "FFmpeg is required for MP3/M4A downloads.\n\n"
                "Use the app's FFmpeg Setup section to choose your ffmpeg binary, "
                "or install it with: brew install ffmpeg"
            )
        elif "operation not permitted" in error_msg.lower() or "permission denied" in error_msg.lower():
            error_msg = (
                "macOS blocked access to the selected folder.\n\n"
                "If you are saving to Downloads, rebuild the app with the updated spec, "
                "then allow Downloads access when macOS prompts."
            )
            
        return {
            'success': False,
            'title': None,
            'filepath': None,
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
