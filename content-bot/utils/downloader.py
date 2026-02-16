# downloader.py - Download video & extract audio
"""
Modul untuk mendownload audio/video dari YouTube
Optimized: Download audio dulu untuk transkripsi, video segment kemudian
"""
import sys
import os
import json
import yt_dlp
from pathlib import Path
from urllib.parse import urlparse
import yt_dlp
from yt_dlp.utils import download_range_func


def validate_youtube_url(url: str):
    """
    Validate that the URL is a legitimate YouTube URL to prevent SSRF/local file access.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

        allowed_domains = ["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"]
        if parsed.netloc.lower() not in allowed_domains:
            raise ValueError(f"Invalid domain: {parsed.netloc}")
    except ValueError as e:
        raise ValueError(f"Security validation failed: {str(e)}")
    except Exception as e:
        raise ValueError(f"Invalid URL format: {str(e)}")


def download_audio_only(url: str, output_dir: str) -> str:
    """
    Download audio saja dari YouTube (lebih cepat & hemat storage)
    
    Args:
        url: YouTube URL
        output_dir: Directory untuk menyimpan audio
        
    Returns:
        Path ke file audio yang didownload
    """
    validate_youtube_url(url)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_template = str(output_dir / "%(title)s.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True,
    }
    
    print(f"[DL] Downloading audio from: {url}")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # The downloaded file path is typically in requested_downloads
            if 'requested_downloads' in info and info['requested_downloads']:
                output_path = info['requested_downloads'][0]['filepath']
            else:
                # Fallback: calculate expected filename
                # Note: prepare_filename returns the name BEFORE post-processing (e.g. .webm)
                # But we know we are converting to mp3
                original_filename = ydl.prepare_filename(info)
                output_path = str(Path(original_filename).with_suffix('.mp3'))

            print(f"[OK] Audio downloaded: {output_path}")
            return output_path

    except Exception as e:
        raise Exception(f"yt-dlp error: {str(e)}")


def download_video_segment(url: str, start: float, end: float, output_path: str) -> str:
    """
    Download hanya segment video tertentu (hemat bandwidth)
    
    Args:
        url: YouTube URL
        start: Start time in seconds
        end: End time in seconds
        output_path: Path untuk output video
        
    Returns:
        Path ke file video segment
    """
    validate_youtube_url(url)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format time as HH:MM:SS for display (optional)
    start_str = _seconds_to_hhmmss(start)
    end_str = _seconds_to_hhmmss(end)
    
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'outtmpl': str(output_path),
        'download_ranges': download_range_func(None, [(start, end)]),
        'force_keyframes_at_cuts': True,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
    }

    print(f"[DL] Downloading video segment: {start_str} - {end_str}")
    
    try:
        # Optimized: Use direct yt_dlp library call instead of subprocess
        # This avoids process creation overhead and provides better error handling
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print(f"[OK] Video segment downloaded: {output_path}")
        return str(output_path)

    except Exception as e:
        raise Exception(f"yt-dlp error: {str(e)}")


def get_video_info(url: str) -> dict:
    """
    Get video metadata (title, duration, etc.)
    
    Args:
        url: YouTube URL
        
    Returns:
        Dictionary dengan info video
    """
    validate_youtube_url(url)

    # Optimized: Use direct yt_dlp library call instead of subprocess
    # This avoids process creation overhead, especially critical for frequent metadata checks
    ydl_opts = {
        'dump_single_json': True,
        'extract_flat': 'in_playlist',
        'noplaylist': True,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return {
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unknown"),
            "description": info.get("description", ""),
            "thumbnail": info.get("thumbnail", ""),
        }
    except Exception as e:
        raise Exception(f"yt-dlp error: {str(e)}")


def _seconds_to_hhmmss(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # Quick test
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    try:
        info = get_video_info(test_url)
        print(f"Video: {info['title']} ({info['duration']}s)")
    except Exception as e:
        print(f"Error: {e}")
