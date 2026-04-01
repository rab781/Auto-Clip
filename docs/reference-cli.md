# Reference: CLI Options

This document describes the Command Line Interface (CLI) options available for Auto-Clip Bot V2 (`main.py`).

## Usage

```bash
python main.py [url] [options]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `url` | Yes | The YouTube video URL you want to process. (You can provide this as a positional argument or using the `--url` flag). |

## Options

| Flag | Description |
|------|-------------|
| `-h`, `--help` | Show the help message and exit. |
| `-u URL`, `--url URL` | YouTube video URL (alternative to the positional argument). |
| `-d`, `--dry-run` | Analyze the video and print potential clips without downloading or processing the actual video files. Useful for testing AI selection logic. |
| `--debug` | Enable debug mode. Shows detailed stack traces if an error occurs during processing. |

## Examples

Process a video using a positional argument:
```bash
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Process a video using the `--url` flag:
```bash
python main.py --url https://youtu.be/dQw4w9WgXcQ
```

Run a dry-run analysis:
```bash
python main.py --url https://youtu.be/dQw4w9WgXcQ --dry-run
```
