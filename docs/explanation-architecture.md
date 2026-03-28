# Explanation: Architecture Overview

Auto-Clip Bot V2 transforms long-form horizontal videos into short-form vertical content. It orchestrates a pipeline of discrete tasks that leverage external APIs and system utilities. You learn how the bot operates and where you customize it by understanding this architecture.

## The Pipeline

The bot follows a linear, multi-phase pipeline:

1.  **Info & Download**: The bot extracts metadata about the YouTube video using `yt-dlp`. To optimize performance, the bot downloads only the audio stream rather than the full video file. This saves bandwidth and local storage, as the bot only needs the high-resolution video for the final generated clips, not the analysis phase.
2.  **Transcription**: The bot passes the downloaded audio to a Whisper model (`faster-whisper-large-v3-turbo-ct2`) running on the Chutes API. This step generates a highly accurate, word-level transcript. The bot uses the word-level timestamps to generate animated captions later.
3.  **AI Analysis**: The bot sends the full transcript to a large language model (`DeepSeek-V3`) via the Chutes API. The LLM analyzes the text to identify narrative arcs, "hooks," and potentially viral moments based on your configuration (such as `min_clip_duration` and `max_clip_duration`). It returns a structured list of potential clips.
4.  **Processing**: This is the most resource-intensive phase. The bot uses FFmpeg to process each clip identified by the AI:
    *   **Segment Download**: The bot downloads the specific segment of the video required for the clip.
    *   **Cropping**: The bot crops the video from horizontal (16:9) to vertical (9:16). If the `FaceTracker` module detects a face using MediaPipe, the bot applies a "smart crop" centered on the subject. If face tracking fails or is unavailable, it falls back to a center crop.
    *   **Captioning**: The bot generates a subtitle file using the word-level transcript timestamps. For animated captions, it creates an `.ass` file that highlights words as they are spoken. For simple captions, it creates an `.srt` file. The bot then burns (hardcodes) these captions into the video frames.
    *   **Audio Mixing**: The bot selects background music (BGM) based on the clip's assigned "mood" and mixes it with the original audio track.

## Single-Pass Processing

To maximize performance, the Processing phase executes cropping, captioning, and audio mixing in a single, optimized FFmpeg filter graph (a "single-pass" process). This approach significantly reduces disk I/O and processing time compared to rendering intermediate files for each step.

If the complex filter graph fails (due to an unsupported font or specific video characteristics), the bot uses a fallback mechanism that processes the video sequentially (converting to vertical, then adding captions, then mixing audio).