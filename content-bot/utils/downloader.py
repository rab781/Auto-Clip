# downloader.py - Download video & extract audio
"""
Modul untuk mendownload audio/video dari YouTube
Optimized: Download audio dulu untuk transkripsi, video segment kemudian
"""
import subprocess
import sys
import os
from pathlib import Path


def download_audio_only(url: str, output_dir: str) -> str:
    """
    Download audio saja dari YouTube (lebih cepat & hemat storage)
    
    Args:
        url: YouTube URL
        output_dir: Directory untuk menyimpan audio
        
    Returns:
        Path ke file audio yang didownload
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_template = str(output_dir / "%(title)s.%(ext)s")
    
    cmd = [
        sys.executable, "-m", "yt_dlp",  # Use python -m for Windows compatibility
        "-x",  # Extract audio only
        "--audio-format", "mp3",
        "--audio-quality", "192K",
        "-o", output_template,
        "--no-playlist",
        "--print", "after_move:filepath",  # Print final path
        url
    ]
    
    print(f"📥 Downloading audio from: {url}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"yt-dlp error: {result.stderr}")
    
    # Get the output file path from stdout
    output_path = result.stdout.strip().split('\n')[-1]
    print(f"✅ Audio downloaded: {output_path}")
    
    return output_path


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
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format time as HH:MM:SS
    start_str = _seconds_to_hhmmss(start)
    end_str = _seconds_to_hhmmss(end)
    
    cmd = [
        sys.executable, "-m", "yt_dlp",  # Use python -m for Windows compatibility
        "--download-sections", f"*{start_str}-{end_str}",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        "--no-playlist",
        "--force-keyframes-at-cuts",  # Precise cutting
        url
    ]
    
    print(f"📥 Downloading video segment: {start_str} - {end_str}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"yt-dlp error: {result.stderr}")
    
    print(f"✅ Video segment downloaded: {output_path}")
    return str(output_path)


def get_video_info(url: str) -> dict:
    """
    Get video metadata (title, duration, etc.)
    
    Args:
        url: YouTube URL
        
    Returns:
        Dictionary dengan info video
    """
    cmd = [
        sys.executable, "-m", "yt_dlp",  # Use python -m for Windows compatibility
        "--dump-json",
        "--no-download",
        "--no-playlist",
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"yt-dlp error: {result.stderr}")
    
    import json
    info = json.loads(result.stdout)
    
    return {
        "title": info.get("title", "Unknown"),
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader", "Unknown"),
        "description": info.get("description", ""),
        "thumbnail": info.get("thumbnail", ""),
    }


def _seconds_to_hhmmss(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # Quick test
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    info = get_video_info(test_url)
    print(f"Video: {info['title']} ({info['duration']}s)")
