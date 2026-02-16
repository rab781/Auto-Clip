# utils/__init__.py
"""
Auto-Clip Utils Package
"""
from .downloader import (
    download_audio_only,
    download_video_segment,
    get_video_info,
    validate_youtube_url
)
from .ai_logic import (
    transcribe_audio, analyze_content_for_clips, generate_clip_caption,
    translate_segments, validate_dependencies, api_retry
)
from .processor import (
    convert_to_vertical,
    burn_captions,
    add_background_music,
    generate_thumbnail,
    create_final_clip,
    select_bgm_by_mood,
    generate_srt_from_segments,
)

__all__ = [
    # Downloader
    "download_audio_only",
    "download_video_segment",
    "get_video_info",
    "validate_youtube_url",
    # AI
    "transcribe_audio",
    "analyze_content_for_clips",
    "generate_clip_caption",
    "translate_segments",
    "validate_dependencies",
    "api_retry",
    # Processor
    "convert_to_vertical",
    "burn_captions",
    "add_background_music",
    "generate_thumbnail",
    "create_final_clip",
    "select_bgm_by_mood",
    "generate_srt_from_segments",
]
