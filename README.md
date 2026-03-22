# Auto-Clip Bot V2

> Transform long-form YouTube videos into viral, vertical short-form clips with AI-powered analysis and dynamic word-level captions.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Why This Exists

Creating short-form content from long-form videos burns hours of your time. You must manually download videos, scrub timelines to find engaging moments, reframe the video for mobile screens, and painstakingly sync word-by-word captions to maintain viewer retention. Auto-Clip Bot completely eliminates this chore. It automates the entire pipeline from transcription to clip selection, turning hours of tedious video editing into a single terminal command.

## Quick Start

```bash
git clone https://github.com/yourusername/auto-clip-bot.git
cd auto-clip-bot
pip install -r content-bot/requirements.txt
cp .env.example .env
# Edit .env and add your CHUTES_API_KEY
python content-bot/main.py https://www.youtube.com/watch?v=YOUR_VIDEO_ID
```

After running this command, you receive fully processed, vertical video clips with captions in the `content-bot/assets/output/` directory.

## Installation

**Prerequisites**:
- Python 3.8+
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system's PATH.

First, clone the repository and navigate into it:
```bash
git clone https://github.com/yourusername/auto-clip-bot.git
cd auto-clip-bot
```

Next, create and activate a virtual environment to keep your dependencies isolated:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, you use `venv\Scripts\activate`
```

Then, install the required Python packages:
```bash
pip install -r content-bot/requirements.txt
```

Finally, configure your API keys. You need a [Chutes.ai](https://chutes.ai) API key to power the DeepSeek LLM for analysis. Create a `.env` file in the root directory and add your key:
```bash
echo "CHUTES_API_KEY=your_chutes_api_key_here" > .env
```

## Usage

### Basic Example

You generate clips from a single YouTube video by running the main pipeline. The bot downloads the audio, transcribes it, identifies the most engaging moments, and renders vertical clips directly to your output directory.

```bash
python content-bot/main.py https://youtu.be/dQw4w9WgXcQ
```

### Configuration

You configure the bot's behavior by modifying `content-bot/config.py`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_width` | `number` | `1080` | Width of the final vertical clip |
| `output_height` | `number` | `1920` | Height of the final vertical clip |
| `min_clip_duration` | `number` | `15` | Minimum duration in seconds for a generated clip |
| `max_clip_duration` | `number` | `300` | Maximum duration in seconds for a complete narrative arc |
| `max_filesize` | `string` | `"500MB"` | Maximum video size to download (DoS protection) |
| `font` | `string` | `"Segoe UI Semibold"` | Font used for the word-level captions |
| `style` | `string` | `"animated"` | Caption style (`animated` for ASS highlighting, `simple` for standard SRT) |
| `highlight_color` | `string` | `"&H00FFFF"` | Color for the currently spoken word (ASS Hex, BGR format: Yellow) |

### Advanced Usage

#### Dry Run Mode
You evaluate which clips the AI selects without spending time or bandwidth to download and process the video files. Use the `--dry-run` flag to test and tweak the AI selection logic.

```bash
python content-bot/main.py --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

#### Debug Mode
You capture detailed stack traces for troubleshooting when an issue occurs by using the `--debug` flag.

```bash
python content-bot/main.py https://youtu.be/dQw4w9WgXcQ --debug
```

## Architecture Overview

The pipeline executes in several distinct phases:
1. **Info & Download**: Extracts metadata via `yt-dlp` and downloads the audio stream.
2. **Transcription**: Uses Whisper (`faster-whisper-large-v3-turbo-ct2`) to generate a highly accurate transcript with word-level timestamps.
3. **AI Analysis**: Passes the transcript to an LLM (`DeepSeek-V3`) to identify narrative arcs, hooks, and viral moments.
4. **Processing**: Uses `ffmpeg-python` and optimized filter graphs to simultaneously crop the video. It incorporates face tracking with a fallback to center crop, burns in animated subtitles (`.ass`), and mixes background music into a final `[vout]` stream.

## Troubleshooting

If you see `RuntimeError: Missing CHUTES_API_KEY`, ensure you create a `.env` file in the project root containing `CHUTES_API_KEY=your_key_here`.

If you see `ffmpeg: command not found`, you do not have FFmpeg installed or it is not in your system's PATH. Install FFmpeg from [the official website](https://ffmpeg.org/download.html) and verify your installation by running `ffmpeg -version` in your terminal.

If you see `ModuleNotFoundError: No module named 'yt_dlp'`, ensure you activate your virtual environment and run `pip install -r content-bot/requirements.txt` from the project root.

If your download hangs or fails on large videos, you likely hit a resource limit or the video exceeds the configured size. Adjust the `max_filesize` setting in `content-bot/config.py` or try processing a shorter video.

## Contributing

You contribute to the project by opening issues and submitting pull requests. For major changes, please open an issue first to discuss your proposed changes.

Ensure you run tests before submitting your code:
```bash
PYTHONPATH=content-bot python3 content-bot/run_tests.py
```

## License

MIT © [Your Name / Organization](https://github.com/yourusername)
