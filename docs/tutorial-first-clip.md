# Tutorial: Your First Viral Clip in 10 Minutes

**What you'll build**: A vertical short-form clip (like a TikTok, Reel, or Short) generated automatically from a long-form YouTube video. The final video has smart cropping, dynamic word-by-word captions, and background music.

**What you'll learn**:
- How to set up Auto-Clip Bot V2
- How to run a dry-run analysis
- Where to find and how to use your generated clips

**Prerequisites**:
- [ ] Python 3.8+ installed
- [ ] [FFmpeg](https://ffmpeg.org/download.html) installed and in your system PATH
- [ ] An account at [Chutes.ai](https://chutes.ai) to get your API key

---

## Step 1: Set Up Your Project

First, you clone the repository and set up your Python environment. You use a separate virtual environment to isolate the project's dependencies from your main system.

```bash
git clone https://github.com/yourusername/auto-clip-bot.git
cd auto-clip-bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

You see `(venv)` at the beginning of your terminal prompt.

> **Tip**: If you see `Error: ENOENT` or path-related errors, ensure you run these commands from the correct directory.

## Step 2: Install Dependencies and Configure Credentials

You install the required Python packages and configure your Chutes API key. The bot uses Chutes for both transcription (Whisper) and narrative analysis (DeepSeek-V3).

```bash
pip install -r content-bot/requirements.txt
cp .env.example .env
```

You open the `.env` file in your text editor and replace the placeholder with your actual Chutes API key:

```env
CHUTES_API_KEY=your_actual_api_key_here
```

> **Tip**: If you see FFmpeg errors later, you ensure you can run `ffmpeg -version` in your terminal. If the command fails, FFmpeg is not in your system PATH.

## Step 3: Run a Dry Run (Analysis Only)

Before downloading large video files, you analyze the video to see what the AI recommends. A dry run fetches the transcript, identifies narrative arcs, and prints potential clips without processing them. This saves time and bandwidth while tweaking selection parameters.

```bash
python content-bot/main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --dry-run
```

You see output similar to this:

```
[AUTO-CLIP BOT V2] Pipeline Starting
   [DRY RUN] Analyze only, no processing
...
   Found 3 potential clips:
   1. [45s - 105s] (60s) The Unexpected Twist
      [HOOK] Hook: "You will not believe what happens next..."
...
```

## Step 4: Generate Your Clip

Now, you remove the `--dry-run` flag to actually download, crop, caption, and render the video.

```bash
python content-bot/main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

The bot executes the full pipeline:
1. Downloads the audio and transcribes it.
2. Finds the most engaging narrative arcs.
3. Downloads the specific video segments.
4. Smart-crops the video to 9:16.
5. Burns animated, word-level captions.
6. Mixes background music.

## Step 5: What You Built

You successfully transformed a horizontal, long-form YouTube video into a ready-to-upload vertical short!

Here is what you learned:
- **Project Setup**: How to initialize the bot and configure your AI provider.
- **Dry Runs**: How to preview AI selections to save time and bandwidth.
- **Automated Processing**: How the bot combines FFmpeg and LLM logic to output vertical media.

You check the `content-bot/assets/output/` directory for your final `.mp4` files, thumbnails, and generated social media captions.

## Next Steps

- [Reference: Configuration Options](reference-configuration.md)
- [How-to: Configure the Bot](how-to-configure.md)
- [Explanation: Architecture Overview](explanation-architecture.md)