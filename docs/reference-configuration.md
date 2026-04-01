# Reference: Configuration Options

This document describes all configuration options from `content-bot/config.py`. You modify these options to customize the bot's behavior.

## API Configuration

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `CHUTES_API_KEY` | API | `None` | Your Chutes.ai API key. Set via `.env`. |
| `CHUTES_BASE_URL` | API | `"https://llm.chutes.ai/v1"` | Base URL for Chutes.ai API endpoints. |

## Model Configuration

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `WHISPER_MODEL` | Model | `"deepdml/faster-whisper-large-v3-turbo-ct2"` | Model used for audio transcription. |
| `LLM_MODEL` | Model | `"deepseek-ai/DeepSeek-V3-0324"` | LLM used for clip selection and reasoning. |

## Video Settings

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `output_width` | Video Settings | `1080` | Width of the final vertical clip. |
| `output_height` | Video Settings | `1920` | Height of the final vertical clip. |
| `fps` | Video Settings | `30` | Frames per second for the final video. |
| `min_clip_duration` | Video Settings | `15` | Minimum duration (seconds) for a generated clip. |
| `max_clip_duration` | Video Settings | `300` | Maximum duration (seconds) for a complete narrative arc. |

## Download Limits

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `max_filesize` | Download Limits | `500MB` | Maximum video size to download (DoS protection). |
| `max_duration` | Download Limits | `3600` | Maximum video duration (seconds) to process. |

## Audio Settings

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `bgm_volume` | Audio Settings | `0.15` | Volume level for background music (15%). |
| `original_audio_volume` | Audio Settings | `1.0` | Volume level for original video audio (100%). |

## Caption Styling

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `font` | Caption Styling | `"Segoe UI Semibold"` | Font used for the word-level captions. |
| `font_size` | Caption Styling | `72` | Font size for captions. |
| `font_color` | Caption Styling | `"white"` | Text color for the subtitles. |
| `outline_color` | Caption Styling | `"black"` | Color for the text outline. |
| `outline_width` | Caption Styling | `3` | Width of the text outline. |
| `shadow_depth` | Caption Styling | `2` | Depth of the text shadow. |
| `position` | Caption Styling | `"bottom"` | Position of the subtitles on screen. |
| `margin_bottom` | Caption Styling | `120` | Margin from the bottom edge of the screen. |
| `words_per_line` | Caption Styling | `2` | Number of words per subtitle line (~1 second interval). |
| `style` | Caption Styling | `"animated"` | Caption style (`animated` for ASS highlighting, `simple` for standard SRT). |
| `highlight_color` | Caption Styling | `"&H00FFFF"` | Color for the currently spoken word (ASS Hex, BGR format: Yellow). |
