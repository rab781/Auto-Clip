# Reference: Configuration Options

This document describes the most commonly used configuration options from `content-bot/config.py`. For the complete and authoritative list of options, including any that are not covered here, you refer directly to `content-bot/config.py` and its inline comments. You modify these options to customize the bot's behavior.

## Video Settings

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `output_width` | Video Settings | `1080` | Width of the final vertical clip. |
| `output_height` | Video Settings | `1920` | Height of the final vertical clip. |
| `min_clip_duration` | Video Settings | `15` | Minimum duration (seconds) for a generated clip. |
| `max_clip_duration` | Video Settings | `300` | Maximum duration (seconds) for a complete narrative arc. |

## Download Limits

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `max_filesize` | Download Limits | `500MB` | Maximum video size to download (DoS protection). |

## Caption Styling

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `font` | Caption Styling | `"Segoe UI Semibold"` | Font used for the word-level captions. |
| `style` | Caption Styling | `"animated"` | Caption style (`animated` for ASS highlighting, `simple` for standard SRT). |
| `highlight_color` | Caption Styling | `"&H00FFFF"` | Color for the currently spoken word (ASS Hex, BGR format: Yellow). |
