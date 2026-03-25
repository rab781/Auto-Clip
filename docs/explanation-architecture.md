# Explanation: Architecture Overview

Auto-Clip Bot V2 transforms long-form horizontal videos into short-form vertical content. It does this by orchestrating a pipeline of discrete tasks that leverage external APIs and system utilities. Understanding this architecture helps clarify how the bot operates and where you might customize it.

## The Pipeline

The bot's architecture follows a linear, multi-phase pipeline:

1.  **Info & Download**: The pipeline begins by extracting metadata about the YouTube video using `yt-dlp`. To optimize performance, the bot then downloads only the audio stream rather than the full video file. This saves bandwidth and local storage, as the high-resolution video is only needed for the final generated clips, not the analysis phase.
2.  **Transcription**: The downloaded audio is passed to a Whisper model (`faster-whisper-large-v3-turbo-ct2`) running on the Chutes API. This step generates a highly accurate, word-level transcript. The word-level timestamps are critical for the animated captions generated later.
3.  **AI Analysis**: The full transcript is sent to a large language model (`DeepSeek-V3`), also via the Chutes API. The LLM analyzes the text to identify narrative arcs, "hooks," and potentially viral moments based on the configuration (such as `min_clip_duration` and `max_clip_duration`). It returns a structured list of these potential clips.
4.  **Processing**: This is the most resource-intensive phase, handled primarily by FFmpeg. For each clip identified by the AI, the bot performs the following actions:
    *   **Segment Download**: It downloads the specific segment of the video required for the clip.
    *   **Cropping**: The video is cropped from horizontal (16:9) to vertical (9:16). If the `FaceTracker` module (using MediaPipe) is available and detects a face, it applies a "smart crop" centered on the subject. If face tracking fails or is unavailable, it falls back to a center crop.
    *   **Captioning**: Using the word-level transcript timestamps, it generates a subtitle file. For animated captions, it creates an `.ass` file that highlights words as they are spoken. For simple captions, it creates an `.srt` file. These captions are then "burned in" (hardcoded) into the video frames.
    *   **Audio Mixing**: Background music (BGM) selected based on the clip's assigned "mood" is mixed with the original audio track.

## Single-Pass Processing

To maximize performance, the Processing phase attempts to execute the cropping, captioning, and audio mixing in a single, optimized FFmpeg filter graph (a "single-pass" process). This approach significantly reduces disk I/O and processing time compared to rendering intermediate files for each step.

If the complex filter graph fails (for example, due to an unsupported font or specific video characteristics), the system includes a robust fallback mechanism that processes the video sequentially (converting to vertical, then adding captions, then mixing audio).