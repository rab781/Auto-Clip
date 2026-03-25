# Auto-Clip Bot V2

> Transform long-form YouTube videos into viral, vertical short-form clips with AI-powered analysis and dynamic word-level captions.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Why This Exists

Creating short-form content from long-form videos is a highly manual, time-consuming process that requires downloading, scrubbing, cropping, and captioning. Auto-Clip Bot automates this entire pipeline, turning a multi-hour chore into a single terminal command so you can focus on publishing.

## Quick Start

```bash
git clone https://github.com/yourusername/auto-clip-bot.git
cd auto-clip-bot
pip install -r content-bot/requirements.txt
cp .env.example .env
```

Set your API key in `.env`:
```env
CHUTES_API_KEY=your_real_key_here
```

Run the bot:
```bash
python content-bot/main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Installation

**Prerequisites**: Python 3.8+, [FFmpeg](https://ffmpeg.org/download.html) (in system PATH)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/auto-clip-bot.git
cd auto-clip-bot

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r content-bot/requirements.txt

# 4. Configure your API key
cp .env.example .env
# Edit .env and add your Chutes.ai API key:
# CHUTES_API_KEY=your_chutes_api_key_here
```

## Usage

### Basic Example

Process a single YouTube video. The bot downloads the audio, transcribes it, analyzes it for engaging moments, and processes those moments into vertical clips.

```bash
python content-bot/main.py https://youtu.be/dQw4w9WgXcQ
```

### Configuration

Customize the bot's behavior by modifying `content-bot/config.py`.

| Option | Category | Default | Description |
|--------|----------|---------|-------------|
| `output_width` | Video Settings | `1080` | Width of the final vertical clip. |
| `output_height` | Video Settings | `1920` | Height of the final vertical clip. |
| `min_clip_duration` | Video Settings | `15` | Minimum duration (seconds) for a generated clip. |
| `max_clip_duration` | Video Settings | `300` | Maximum duration (seconds) for a complete narrative arc. |
| `max_filesize` | Download Limits | `500MB` | Maximum video size to download (DoS protection). |
| `font` | Caption Styling | `"Segoe UI Semibold"` | Font used for the word-level captions. |
| `style` | Caption Styling | `"animated"` | Caption style (`animated` for ASS highlighting, `simple` for standard SRT). |
| `highlight_color` | Caption Styling | `"&H00FFFF"` | Color for the currently spoken word (ASS Hex, BGR format: Yellow). |

### Advanced Usage

#### Dry Run Mode

See what clips the AI selects without downloading and processing the video files. This is excellent for testing and tweaking the AI selection logic.

```bash
python content-bot/main.py --url https://youtu.be/dQw4w9WgXcQ --dry-run
```

#### Debug Mode

Show detailed stack traces for troubleshooting if you encounter an issue.

```bash
python content-bot/main.py https://youtu.be/dQw4w9WgXcQ --debug
```

## Documentation

- [Tutorial: Your First Viral Clip](docs/tutorial-first-clip.md)
- [Explanation: Architecture Overview](docs/explanation-architecture.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT © [Your Name / Organization](https://github.com/yourusername)
