# animated_captions.py - Advanced Subtitle Generator
"""
Modul untuk generate subtitle format ASS (Advanced Substation Alpha)
dengan animasi word-by-word (Karaoke/Highlight style) ala CapCut/TikTok.
"""
from utils.time_utils import format_timestamp

def sanitize_ass_text(text: str) -> str:
    """
    Sanitize text for ASS format by replacing special characters
    with full-width equivalents to prevent tag injection.
    """
    return text.replace("{", "｛").replace("}", "｝").replace("\\", "＼")

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
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{primary_color},{primary_color},{outline_color},{back_color},1,0,0,0,100,100,0,0,1,{outline_width},{shadow_depth},2,50,50,{margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    words_per_batch = settings.get("words_per_line", 2)
    
    for seg in segments:
        seg_start = seg["start"]
        seg_end = seg["end"]
        text = seg["text"].strip()
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
            
            for i in range(len(batch_words)):
                # Timing for this specific highlight frame
                frame_start = batch_start_time + (i * time_per_batch_word)
                frame_end = batch_start_time + ((i + 1) * time_per_batch_word)
                
                # Construct text with highlight tags
                formatted_text = ""
                for j, w in enumerate(batch_words):
                    w_sanitized = sanitize_ass_text(w)
                    if j == i:
                        # Active word: Highlight color + scale up for pop effect
                        formatted_text += f"{{\\c{highlight_color}\\fscx120\\fscy120}}{w_sanitized}{{\\c{primary_color}\\fscx100\\fscy100}} "
                    else:
                        formatted_text += f"{w_sanitized} "
                
                formatted_text = formatted_text.strip()
                
                start_str = format_timestamp(frame_start, 'ass')
                end_str = format_timestamp(frame_end, 'ass')
                
                ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{formatted_text}\n"
            
            current_word_idx += words_per_batch

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
        
    return output_path
