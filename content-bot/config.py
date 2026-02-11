# config.py - Centralized Configuration
"""
Konfigurasi terpusat untuk Auto-Clip Bot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === API Configuration ===
CHUTES_API_KEY = os.getenv("CHUTES_API_KEY")
CHUTES_BASE_URL = "https://llm.chutes.ai/v1"

# === Model Configuration ===
WHISPER_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"  # Fast & accurate
LLM_MODEL = "deepseek-ai/DeepSeek-V3-0324"  # Strong reasoning untuk clip selection

# === Paths ===
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
DOWNLOADS_DIR = ASSETS_DIR / "downloads"
TEMP_DIR = ASSETS_DIR / "temp"
OUTPUT_DIR = ASSETS_DIR / "output"
BGM_DIR = ASSETS_DIR / "bgm"

# Create directories if not exist
for dir_path in [DOWNLOADS_DIR, TEMP_DIR, OUTPUT_DIR, BGM_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# === Video Processing Settings ===
VIDEO_SETTINGS = {
    "output_width": 1080,
    "output_height": 1920,
    "fps": 30,
    "min_clip_duration": 15,  # Minimum duration for a clip
    "max_clip_duration": 300,  # maximum 5 menit (300 detik) untuk narrative arc lengkap
}

# === Audio Settings ===
AUDIO_SETTINGS = {
    "bgm_volume": 0.15,  # 15% volume untuk BGM
    "original_audio_volume": 1.0,
}

# === Caption Settings (Word-level Subtitle Style) ===
CAPTION_SETTINGS = {
    "font": "Segoe UI Semibold",  # Modern font (available on Windows)
    "font_size": 72,  # Large size for 1920p ASS resolution (CapCut-style)
    "font_color": "white",
    "outline_color": "black",
    "outline_width": 3,  # Thicker outline for readability
    "shadow_depth": 2,  # Deeper shadow for contrast
    "position": "bottom",
    "margin_bottom": 120,  # Higher margin from bottom edge
    "words_per_line": 2,  # 2 kata per subtitle entry (~1 detik interval)
    "style": "animated",  # "simple" (SRT) or "animated" (ASS with word highlight)
    "highlight_color": "&H00FFFF",  # Yellow in ASS hex format (BGR)
}
