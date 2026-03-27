# animated_captions.py - Advanced Subtitle Generator
"""
Modul untuk generate subtitle format ASS (Advanced Substation Alpha)
dengan animasi word-by-word (Karaoke/Highlight style) ala CapCut/TikTok.
"""
from utils.time_utils import format_timestamp

def sanitize_ass_text(text: str) -> str:
    """
    Sanitize text to prevent ASS injection.
    Replaces special characters with full-width equivalents.
    """
    return text.replace('{', '｛').replace('}', '｝').replace('\\', '＼')

def generate_animated_ass(segments: list, output_path: str, settings: dict) -> str:
    """
    Generate ASS file with word-level highlighting.
    
    Args:
        segments: List of dicts {start, end, text}
        output_path: Path to save .ass file
        settings: Dict from config (CAPTION_SETTINGS)
        
    Returns:
        Path to generated .ass file
    """
    
    # Extract settings
    font = settings.get("font", "Segoe UI Semibold")
    font_size = settings.get("font_size", 72)
    outline_width = settings.get("outline_width", 3)
    shadow_depth = settings.get("shadow_depth", 2)
    margin_bottom = settings.get("margin_bottom", 120)
    
    # ASS color format: &HBBGGRR
    primary_color = "&H00FFFFFF"  # White
    outline_color = "&H00000000"  # Black
    back_color = "&H80000000"     # Semi-transparent black background
    highlight_color = settings.get("highlight_color", "&H0000FFFF")  # Yellow (BGR)
    
    # Header
    ass_lines = []
    ass_lines.append(f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{primary_color},{primary_color},{outline_color},{back_color},1,0,0,0,100,100,0,0,1,{outline_width},{shadow_depth},2,50,50,{margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")

    words_per_batch = settings.get("words_per_line", 2)
    
    # ⚡ Bolt Optimization: Constant highlight tag pre-calculation
    # Impact: Avoids redundant string formatting and memory allocation for every highlighted word
    highlight_prefix = f"{{\\c{highlight_color}\\fscx120\\fscy120}}"
    highlight_suffix = f"{{\\c{primary_color}\\fscx100\\fscy100}}"

    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        text = sanitize_ass_text(seg["text"].strip())
        words = text.split()
        
        if not words:
            continue
            
        num_words = len(words)
        duration = seg_end - seg_start
        time_per_word = duration / max(num_words, 1)
        
        current_word_idx = 0
        while current_word_idx < num_words:
            # Create a batch
            batch_end_idx = min(current_word_idx + words_per_batch, num_words)
            batch_words = words[current_word_idx:batch_end_idx]
            
            # Calculate batch timing
            batch_start_time = seg_start + (current_word_idx * time_per_word)
            batch_end_time = seg_start + (batch_end_idx * time_per_word)
            
            batch_duration = batch_end_time - batch_start_time
            time_per_batch_word = batch_duration / len(batch_words)
            
            # ⚡ Bolt Optimization: Per-batch timestamp caching
            # Impact: Significantly reduces the number of format_timestamp calls per word frame
            timestamps = [
                format_timestamp(batch_start_time + (k * time_per_batch_word), 'ass')
                for k in range(len(batch_words) + 1)
            ]

            for i in range(len(batch_words)):
                start_str = timestamps[i]
                end_str = timestamps[i+1]
                
                # ⚡ Bolt Optimization: O(1) list mutation pattern for word highlighting
                # Impact: Replaces O(N) list rebuilding and repeated string interpolation per frame
                formatted_words = list(batch_words)
                formatted_words[i] = f"{highlight_prefix}{batch_words[i]}{highlight_suffix}"
                
                formatted_text = " ".join(formatted_words)
                
                ass_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{formatted_text}\n")
            
            current_word_idx += words_per_batch

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(ass_lines))
        
    return output_path
