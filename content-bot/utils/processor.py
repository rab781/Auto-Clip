# processor.py - Video Processing & Editing
"""
Modul untuk memproses video:
- Cutting/trimming video
- Convert ke format vertical 9:16 (Smart Crop / Center Crop)
- Burn captions (hardsub)
- Add background music
- Generate thumbnail
"""
import subprocess
import os
import random
from pathlib import Path
import sys
sys.path.append(str(__file__).rsplit('\\', 2)[0])

from config import (
    VIDEO_SETTINGS, AUDIO_SETTINGS, CAPTION_SETTINGS,
    TEMP_DIR, OUTPUT_DIR, BGM_DIR
)
from utils.animated_captions import generate_animated_ass
from utils.time_utils import format_timestamp

# Try to import FaceTracker for smart crop
try:
    from utils.face_tracker import FaceTracker
    FACE_TRACKER_AVAILABLE = True
except ImportError:
    print("! FaceTracker modules (MediaPipe/OpenCV) not found. Using Center Crop.")
    FACE_TRACKER_AVAILABLE = False


def _get_smart_crop_x(video_path: str, width: int, height: int) -> str:
    """
    Determine the X position for cropping (Smart Crop logic).
    Returns the crop expression string for FFmpeg.
    """
    # Default: Center Crop
    crop_x = "(in_w-out_w)/2"  # Center
    
    # Try Smart Crop
    if FACE_TRACKER_AVAILABLE:
        print(f"[INFO] Analyzing video for Smart Crop: {Path(video_path).name}")
        try:
            tracker = FaceTracker()
            avg_x = tracker.get_average_face_position(str(video_path))
            tracker.close()
            
            if avg_x is not None:
                print(f"   [FACE] Face detected at X={avg_x:.2f}. Applying Smart Crop.")
                crop_x = f"(in_w*{avg_x})-(out_w/2)"
            else:
                print("   [FACE] No face detected. Defaulting to Center Crop.")
        except Exception as e:
            print(f"! Smart Crop failed ({e}). Defaulting to Center Crop.")

    return crop_x


def _get_subtitle_filter_string(srt_path: str) -> str:
    """
    Generate FFmpeg filter string for burning subtitles.
    Handles escaping and ASS vs SRT logic.
    """
    # Escape path for FFmpeg (Windows needs special handling)
    # Also escape single quotes for filter string syntax
    srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:").replace("'", r"'\''")

    # Check if ASS (Animated) or SRT (Simple)
    is_ass = str(srt_path).lower().endswith(".ass")

    if is_ass:
        return f"subtitles='{srt_escaped}'"
    else:
        # SRT requires force_style for customization
        font = CAPTION_SETTINGS["font"]
        font_size = CAPTION_SETTINGS["font_size"]
        outline_width = CAPTION_SETTINGS["outline_width"]
        margin_bottom = CAPTION_SETTINGS.get("margin_bottom", 50)
        shadow_depth = CAPTION_SETTINGS.get("shadow_depth", 1)

        # Position: bottom, word-level subtitle style
        return (
            f"subtitles='{srt_escaped}':"
            f"force_style='FontName={font},"
            f"FontSize={font_size},"
            f"PrimaryColour=&H00FFFFFF,"  # White
            f"OutlineColour=&H00000000,"  # Black outline
            f"BackColour=&H80000000,"  # Semi-transparent black background
            f"Outline={outline_width},"
            f"Shadow={shadow_depth},"
            f"Alignment=2,"  # Center bottom
            f"MarginV={margin_bottom}'"
        )


def _get_audio_mix_filter(duration: float, bgm_volume: float, original_volume: float) -> str:
    """
    Generate FFmpeg filter string for mixing BGM with original audio.
    Assumes [1:a] is BGM and [0:a] is original.
    """
    return (
        f"[1:a]volume={bgm_volume},aloop=loop=-1:size={int(duration*48000)}[bgm];"
        f"[0:a]volume={original_volume}[original];"
        f"[original][bgm]amix=inputs=2:duration=first[aout]"
    )


def convert_to_vertical(video_path: str, output_path: str) -> str:
    """
    Convert video ke aspect ratio 9:16 (vertical/portrait)
    Menggunakan Smart Crop (Face Detection) jika memungkinkan,
    fallback ke Center Crop.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width = VIDEO_SETTINGS["output_width"]
    height = VIDEO_SETTINGS["output_height"]

    crop_x = _get_smart_crop_x(video_path, width, height)

    # FFmpeg filter: Scale -> Crop
    filter_complex = (
        f"scale=-1:{height},"
        f"crop={width}:{height}:{crop_x}:0"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", filter_complex,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-crf", "18",       # High quality (visually lossless)
        "-preset", "slow",   # Better compression efficiency
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    print(f"[CROP] Converting to vertical (9:16)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    
    print(f"[DONE] Vertical video created: {output_path}")
    return str(output_path)


def generate_srt_from_segments(segments: list, output_path: str, words_per_line: int = 3) -> str:
    """
    Generate SRT file dari Whisper segments dengan word-level timing.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    srt_entries = []
    entry_index = 1
    
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        
        seg_start = seg["start"]
        seg_end = seg["end"]
        seg_duration = seg_end - seg_start
        
        # Split text into words
        words = text.split()
        
        if len(words) == 0:
            continue
        
        # Group words into chunks of words_per_line
        word_groups = []
        for i in range(0, len(words), words_per_line):
            word_groups.append(" ".join(words[i:i + words_per_line]))
        
        # Calculate time per group
        if len(word_groups) > 0:
            time_per_group = seg_duration / len(word_groups)
        else:
            continue
        
        for i, group in enumerate(word_groups):
            group_start = seg_start + (i * time_per_group)
            group_end = seg_start + ((i + 1) * time_per_group)
            
            # Minimum 0.5s per entry, maximum matches group timing
            group_end = min(group_end, seg_end)
            
            start_str = format_timestamp(group_start, 'srt')
            end_str = format_timestamp(group_end, 'srt')
            
            srt_entries.append(f"{entry_index}\n{start_str} --> {end_str}\n{group}\n\n")
            entry_index += 1
    
    srt_content = "".join(srt_entries)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    print(f"[SUB] SRT file created ({entry_index - 1} entries, {words_per_line} words/line): {output_path}")
    return str(output_path)


def burn_captions(video_path: str, srt_path: str, output_path: str) -> str:
    """
    Burn captions (hardsub) ke video menggunakan FFmpeg
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    subtitle_filter = _get_subtitle_filter_string(srt_path)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", subtitle_filter,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-crf", "18",       # High quality (visually lossless)
        "-preset", "slow",   # Better compression efficiency
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    print(f"[SUB] Burning captions to video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        # Fallback: tanpa subtitle styling yang kompleks
        print("! Trying simpler subtitle format...")
        # Escape path for simple usage
        srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:").replace("'", r"'\''")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles='{srt_escaped}'",
            "-c:a", "copy",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
    
    print(f"[DONE] Captions burned: {output_path}")
    return str(output_path)


def add_background_music(video_path: str, bgm_path: str, output_path: str, 
                         bgm_volume: float = None) -> str:
    """
    Mix background music dengan audio original video
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if bgm_volume is None:
        bgm_volume = AUDIO_SETTINGS["bgm_volume"]
    
    original_volume = AUDIO_SETTINGS["original_audio_volume"]
    
    # Get video duration
    duration = _get_video_duration(video_path)
    
    filter_complex = _get_audio_mix_filter(duration, bgm_volume, original_volume)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-shortest",
        str(output_path)
    ]
    
    print(f"[MUSIC] Adding background music (volume: {bgm_volume*100:.0f}%)...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    
    print(f"[DONE] BGM added: {output_path}")
    return str(output_path)


def generate_thumbnail(video_path: str, output_path: str, timestamp: float = None) -> str:
    """
    Generate thumbnail dari video
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if timestamp is None:
        duration = _get_video_duration(video_path)
        timestamp = duration / 3  # Ambil frame di 1/3 video
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",  # High quality
        str(output_path)
    ]
    
    print(f"[THUMB] Generating thumbnail at {timestamp:.1f}s...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    
    print(f"[DONE] Thumbnail created: {output_path}")
    return str(output_path)


def select_bgm_by_mood(mood: str) -> str:
    """
    Select BGM file based on mood
    """
    bgm_dir = Path(BGM_DIR)
    
    # Cari file BGM yang match dengan mood
    mood_patterns = {
        "energetic": ["energetic", "upbeat", "hype", "energy"],
        "emotional": ["emotional", "sad", "touching", "piano"],
        "funny": ["funny", "comedy", "quirky", "fun"],
        "dramatic": ["dramatic", "epic", "intense", "cinematic"],
        "chill": ["chill", "lofi", "relax", "calm"],
    }
    
    patterns = mood_patterns.get(mood.lower(), [mood.lower()])
    
    # Cari semua mp3/wav files di BGM folder
    all_bgm = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.wav"))
    
    if not all_bgm:
        print(f"! No BGM files found in {bgm_dir}")
        return None
    
    # Match by filename
    for pattern in patterns:
        matching = [f for f in all_bgm if pattern in f.stem.lower()]
        if matching:
            selected = random.choice(matching)
            print(f"[MUSIC] Selected BGM for '{mood}' mood: {selected.name}")
            return str(selected)
    
    # Fallback: random BGM
    selected = random.choice(all_bgm)
    print(f"[MUSIC] Random BGM selected: {selected.name}")
    return str(selected)


def _create_final_clip_optimized(
    video_path: str,
    srt_path: str,
    bgm_path: str,
    output_path: str,
    bgm_volume: float = None,
    original_volume: float = None
) -> str:
    """
    Optimized single-pass FFmpeg pipeline: Crop -> Caption -> BGM

    Performance Improvement:
    Combines 3 separate FFmpeg passes (vertical conversion, burning captions, mixing audio)
    into a single complex filter graph. This eliminates 2 intermediate re-encoding steps,
    significantly reducing processing time and disk I/O.
    """
    if bgm_volume is None:
        bgm_volume = AUDIO_SETTINGS["bgm_volume"]
    if original_volume is None:
        original_volume = AUDIO_SETTINGS["original_audio_volume"]

    width = VIDEO_SETTINGS["output_width"]
    height = VIDEO_SETTINGS["output_height"]

    # 1. Get Crop Parameter
    crop_x = _get_smart_crop_x(video_path, width, height)

    # 2. Build Filter Complex
    # [0:v] -> scale -> crop -> [v_crop]
    # [v_crop] -> subtitles -> [v_out]

    filters = [
        f"[0:v]scale=-1:{height},crop={width}:{height}:{crop_x}:0[v_crop]"
    ]

    subtitle_filter_str = ""
    if srt_path and Path(srt_path).exists():
         sub_str = _get_subtitle_filter_string(srt_path)
         # Remove "subtitles='path'..." wrapper to use in filter chain correctly?
         # No, wait. subtitle_filter string is "subtitles='path':options"
         # So we can use it directly: [v_crop]subtitles='path'[v_out]
         # But we need to prepend inputs and append output label
         # Wait, filter string from _get_subtitle_filter_string is fully formed "subtitles=..."
         # So: f"[v_crop]{sub_str}[v_out]"
         filters.append(f"[v_crop]{sub_str}[v_out]")
         final_video_map = "[v_out]"
    else:
         # No subtitles, just pass through v_crop as v_out
         final_video_map = "[v_crop]"

    # 3. Audio Mixing
    inputs = ["-i", str(video_path)]
    final_audio_map = "0:a" # Default if no BGM

    if bgm_path and Path(bgm_path).exists():
        inputs.extend(["-i", str(bgm_path)])
        duration = _get_video_duration(video_path)
        audio_filter = _get_audio_mix_filter(duration, bgm_volume, original_volume)
        # Append audio filter to filters list
        # Note: audio filter uses [1:a] and [0:a] and outputs [aout]
        filters.append(audio_filter)
        final_audio_map = "[aout]"

    filter_complex = ";".join(filters)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", final_video_map,
        "-map", final_audio_map,
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        # "-c:a", "aac", # Re-encode audio (implicit with amix usually, but good to specify if needed)
        # But wait, original code used -c:a copy when not mixing.
        # With amix, we must re-encode audio. Default is aac.
        str(output_path)
    ]

    print(f"[OPTIMIZED] Processing clip in single pass...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")

    print(f"[DONE] Optimized clip created: {output_path}")
    return str(output_path)


def create_final_clip(
    video_segment_path: str,
    clip_info: dict,
    segments: list,
    clip_number: int,
    output_dir: str = None
) -> dict:
    """
    Orchestrate full clip processing pipeline:
    1. Convert to vertical
    2. Generate SRT
    3. Burn captions
    4. Add BGM
    5. Generate thumbnail
    
    Args:
        video_segment_path: Path ke video segment
        clip_info: Metadata dari LLM analysis
        segments: Whisper segments untuk clip ini
        clip_number: Nomor clip (untuk naming)
        output_dir: Output directory (default: dari config)
        
    Returns:
        Dictionary dengan paths ke semua output files
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR
    
    output_dir = Path(output_dir)
    temp_dir = Path(TEMP_DIR)
    
    # Generate safe filename dari caption title
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" 
                         for c in clip_info.get("caption_title", f"clip_{clip_number}"))
    safe_title = safe_title[:50].strip() or f"clip_{clip_number}"
    base_name = f"{clip_number:02d}_{safe_title}"
    
    print(f"\n{'='*50}")
    print(f"[ACTION] Processing Clip #{clip_number}: {clip_info.get('caption_title', 'Unknown')}")
    print(f"{'='*50}")
    
    # Step 1: Generate Captions (SRT or ASS) - NEEDED FOR BOTH PIPELINES
    caption_style = CAPTION_SETTINGS.get("style", "simple")
    subtitle_path = None
    
    if segments:
        if caption_style == "animated":
            subtitle_path = temp_dir / f"{base_name}.ass"
            generate_animated_ass(segments, str(subtitle_path), CAPTION_SETTINGS)
            print(f"[SUB] Generated Animated Captions (ASS): {subtitle_path.name}")
        else:
            subtitle_path = temp_dir / f"{base_name}.srt"
            words_per_line = CAPTION_SETTINGS.get("words_per_line", 3)
            generate_srt_from_segments(segments, str(subtitle_path), words_per_line=words_per_line)
    
    # Step 2: Select BGM - NEEDED FOR BOTH PIPELINES
    mood = clip_info.get("mood", "chill")
    bgm_path = select_bgm_by_mood(mood)
    
    final_video_path = output_dir / f"{base_name}.mp4"
    
    # TRY OPTIMIZED PIPELINE
    try:
        _create_final_clip_optimized(
            video_path=video_segment_path,
            srt_path=str(subtitle_path) if subtitle_path else None,
            bgm_path=bgm_path,
            output_path=str(final_video_path)
        )
    except Exception as e:
        print(f"\n! Optimized pipeline failed: {e}")
        print("! Fallback to sequential processing...")

        # FALLBACK: SEQUENTIAL PROCESSING

        # Step 1: Convert to vertical
        vertical_path = temp_dir / f"{base_name}_vertical.mp4"
        vertical_video = convert_to_vertical(video_segment_path, str(vertical_path))

        # Step 2: Burn captions (if subtitle exists)
        if subtitle_path and subtitle_path.exists():
            captioned_path = temp_dir / f"{base_name}_captioned.mp4"
            captioned_video = burn_captions(vertical_video, str(subtitle_path), str(captioned_path))
        else:
            captioned_video = vertical_video

        # Step 3: Add BGM
        if bgm_path:
            add_background_music(captioned_video, bgm_path, str(final_video_path))
        else:
            import shutil
            shutil.copy(captioned_video, final_video_path)
            print("! No BGM added (no matching file found)")

    # Step 5: Generate thumbnail (Step 4 was inside pipeline)
    thumbnail_path = output_dir / f"{base_name}_thumbnail.jpg"
    thumbnail = generate_thumbnail(str(final_video_path), str(thumbnail_path))
    
    # Step 6: Save caption to text file
    caption_path = output_dir / f"{base_name}_caption.txt"
    hook = clip_info.get('hook', '')
    narrative_type = clip_info.get('narrative_type', 'story')
    caption_title = clip_info.get('caption_title', '')
    reason = clip_info.get('reason', '')
    enhanced_caption = clip_info.get('enhanced_caption', '')
    
    # Social media ready caption (from LLM)
    if enhanced_caption:
        caption_text = enhanced_caption
    else:
        caption_text = caption_title
    
    # Also add metadata below for reference
    caption_text += f"\n\n--- METADATA ---\n"
    if hook:
        caption_text += f"🪝 Hook: {hook}\n"
    caption_text += f"📖 {reason}\n"
    caption_text += f"🎬 Type: {narrative_type} | Mood: {mood}\n"
    
    with open(caption_path, "w", encoding="utf-8") as f:
        f.write(caption_text)
    
    print(f"\n[DONE] Clip #{clip_number} complete!")
    print(f"   [VIDEO] Video: {final_video_path.name}")
    print(f"   [THUMB] Thumbnail: {thumbnail_path.name}")
    print(f"   [TEXT] Caption: {caption_path.name}")
    
    return {
        "video": str(final_video_path),
        "thumbnail": str(thumbnail_path),
        "caption_file": str(caption_path),
        "caption_text": caption_text,
        "mood": mood,
    }


def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return 30.0  # Default fallback
    
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 30.0


if __name__ == "__main__":
    print("Processor module loaded successfully!")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"BGM directory: {BGM_DIR}")
