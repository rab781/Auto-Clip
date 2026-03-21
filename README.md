# Auto-Clip Bot V2

> Transform long-form YouTube videos into viral, vertical short-form clips with AI-powered analysis and dynamic word-level captions.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Why This Exists

Creating short-form content (TikToks, Reels, Shorts) from long-form videos is a highly manual, time-consuming process. Creators have to download the video, manually scrub to find engaging moments, crop to a 9:16 aspect ratio, and painfully add word-by-word animated captions to keep viewer retention high. Auto-Clip Bot automates this entire pipeline using AI for transcription, clip selection, and automated FFmpeg processing, turning a multi-hour chore into a single terminal command.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/auto-clip-bot.git
cd auto-clip-bot

# Install dependencies
pip install -r content-bot/requirements.txt

# Set up your environment variables
cp .env.example .env
# Edit .env and add your CHUTES_API_KEY

# Run the bot on a YouTube video
python content-bot/main.py https://www.youtube.com/watch?v=YOUR_VIDEO_ID
```

Your processed, vertical video clips with captions will be saved in `content-bot/assets/output/`.

## Installation

**Prerequisites**:
- Python 3.8 or higher
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system's PATH.

### 1. Clone and Setup Environment

```bash
git clone https://github.com/yourusername/auto-clip-bot.git
cd auto-clip-bot

# Recommended: Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

pip install -r content-bot/requirements.txt
```

### 2. Configure API Keys

The bot uses [Chutes.ai](https://chutes.ai) for the DeepSeek LLM.

1. Create a `.env` file in the root directory.
2. Add your API key:
   ```env
   CHUTES_API_KEY=your_chutes_api_key_here
   ```

## Usage

### Basic Example

The most common use case is processing a single YouTube video. The bot will download the audio, transcribe it, analyze it for the most engaging moments, and process those moments into vertical clips.

```bash
python content-bot/main.py https://youtu.be/dQw4w9WgXcQ
```

### Advanced Usage

#### Dry Run Mode
If you want to see what clips the AI *would* select without actually spending the time to download and process the video files, use the `--dry-run` flag. This is excellent for testing and tweaking the AI selection logic.

```bash
python content-bot/main.py --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

#### Debug Mode
If you encounter an issue and need detailed stack traces for troubleshooting:

```bash
python content-bot/main.py https://youtu.be/dQw4w9WgXcQ --debug
```

### Configuration

You can customize the bot's behavior by modifying `content-bot/config.py`.

| Option Category | Setting | Default | Description |
|-----------------|---------|---------|-------------|
| **Video Settings** | `output_width` | `1080` | Width of the final vertical clip. |
| **Video Settings** | `output_height` | `1920` | Height of the final vertical clip. |
| **Video Settings** | `min_clip_duration` | `15` | Minimum duration (seconds) for a generated clip. |
| **Video Settings** | `max_clip_duration` | `300` | Maximum duration (seconds) for a complete narrative arc. |
| **Download Limits** | `max_filesize` | `500MB` | Maximum video size to download (DoS protection). |
| **Caption Styling** | `font` | `"Segoe UI Semibold"` | Font used for the word-level captions. |
| **Caption Styling** | `style` | `"animated"` | Caption style (`animated` for ASS highlighting, `simple` for standard SRT). |
| **Caption Styling** | `highlight_color` | `"&H00FFFF"` | Color for the currently spoken word (ASS Hex, BGR format: Yellow). |

## Architecture Overview

The pipeline executes in several distinct phases:
1. **Info & Download**: Extracts metadata via `yt-dlp` and downloads the audio stream.
2. **Transcription**: Uses Whisper (`faster-whisper-large-v3-turbo-ct2`) to generate a highly accurate transcript with word-level timestamps.
3. **AI Analysis**: Passes the transcript to an LLM (`DeepSeek-V3`) to identify narrative arcs, "hooks", and viral moments.
4. **Processing**: Uses `ffmpeg-python` and optimized filter graphs to simultaneously crop the video (with face tracking fallback to center crop), burn in animated subtitles (`.ass`), and mix background music into a final `[vout]` stream.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate. Run tests via:
```bash
PYTHONPATH=content-bot python3 content-bot/run_tests.py
```

## License

MIT © [Your Name / Organization](https://github.com/yourusername)
