# main.py - Auto-Clip Pipeline Orchestrator
"""
Auto-Clip Bot - Main Entry Point
Bot otomatis untuk mengubah video YouTube panjang menjadi klip pendek viral

Usage:
    python main.py <youtube_url>
    python main.py --url <youtube_url>
    python main.py --url <youtube_url> --dry-run
"""
import sys
import shutil
import argparse
import concurrent.futures
import bisect
from pathlib import Path
from tqdm import tqdm
import unittest
from unittest import mock

from config import DOWNLOADS_DIR, TEMP_DIR, OUTPUT_DIR
from utils import (
    download_audio_only,
    download_video_segment,
    get_video_info,
    transcribe_audio,
    analyze_content_for_clips,
    generate_clip_caption,
    translate_segments,
    validate_dependencies,
    create_final_clip,
)


def process_single_clip(i: int, clip: dict, url: str, transcription: dict, segment_starts: list) -> dict:
    """
    Process a single clip: download, enhance, translate, and create video.
    Returns the result dict or None if failed.
    """
    try:
        # Download video segment
        segment_path = TEMP_DIR / f"segment_{i}.mp4"
        try:
            download_video_segment(url, clip["start"], clip["end"], str(segment_path))
        except Exception as e:
            print(f"\n! Failed to download segment {i}: {e}")
            return None

        # Extract relevant transcript segments for this clip
        clip_segments = []
        if "segments" in transcription:
            segments = transcription["segments"]
            # Optimization: Use binary search (O(log N)) instead of linear scan (O(N))
            # Find the first segment that starts at or after the clip's start time
            start_idx = bisect.bisect_left(segment_starts, clip["start"])

            for seg_idx in range(start_idx, len(segments)):
                seg = segments[seg_idx]
                # Since segments are sorted by start time, we can stop early if start exceeds clip end
                if seg["start"] > clip["end"]:
                    break

                if seg["end"] <= clip["end"]:
                    clip_segments.append({
                        "start": seg["start"] - clip["start"],
                        "end": seg["end"] - clip["start"],
                        "text": seg["text"]
                    })

        # Generate enhanced caption
        transcript_text = " ".join([s["text"] for s in clip_segments])
        try:
            enhanced_caption = generate_clip_caption(clip, transcript_text)
            clip["enhanced_caption"] = enhanced_caption
        except Exception as e:
            print(f"\n! Caption generation failed: {e}")
            clip["enhanced_caption"] = clip.get("caption_title", "")

        # Translate segments to Indonesian
        if clip_segments:
            try:
                clip_segments = translate_segments(clip_segments)
            except Exception as e:
                print(f"\n! Translation failed, using original text: {e}")

        # Create final clip
        try:
            result = create_final_clip(
                video_segment_path=str(segment_path),
                clip_info=clip,
                segments=clip_segments,
                clip_number=i,
                output_dir=str(OUTPUT_DIR)
            )
            return result
        except Exception as e:
            print(f"\n! Failed to process clip {i}: {e}")
            return None

    except Exception as e:
        print(f"\n! Unexpected error in clip {i}: {e}")
        return None


class ProcessSingleClipTest(unittest.TestCase):
    """
    Focused unit tests for process_single_clip.

    These tests stub out I/O-heavy helpers and validate:
      1) The expected subset of transcript segments is selected for a clip window.
      2) The clip_number passed to create_final_clip remains the original i.
    """

    def test_segment_selection_and_clip_number(self):
        # Arrange: synthetic transcription with segments around the clip window.
        transcription = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "first"},
                {"start": 5.0, "end": 10.0, "text": "second"},
                {"start": 12.0, "end": 15.0, "text": "third"},
            ]
        }
        segment_starts = [s["start"] for s in transcription["segments"]]

        # Clip spans from 4s to 13s: only the second segment should be fully inside
        # according to the current selection logic.
        clip = {
            "start": 4.0,
            "end": 13.0,
            "caption_title": "test clip",
        }
        url = "http://example.com/video"
        clip_index = 2

        with mock.patch(__name__ + ".download_video_segment") as mock_download, \
             mock.patch(__name__ + ".generate_clip_caption") as mock_caption, \
             mock.patch(__name__ + ".translate_segments") as mock_translate, \
             mock.patch(__name__ + ".create_final_clip") as mock_create:

            # download_video_segment is a no-op in this test
            mock_download.return_value = None

            # generate_clip_caption returns a fixed enhanced caption
            mock_caption.return_value = "enhanced caption"

            # translate_segments returns segments unchanged
            mock_translate.side_effect = lambda segs: segs

            def create_side_effect(video_segment_path, clip_info, segments, clip_number, output_dir):
                # Assert clip_number is the original outer index
                self.assertEqual(clip_number, clip_index)

                # Only the second segment should be selected
                self.assertEqual(len(segments), 1)
                seg = segments[0]

                # The times should be relative to clip["start"]
                self.assertAlmostEqual(seg["start"], 5.0 - clip["start"])
                self.assertAlmostEqual(seg["end"], 10.0 - clip["start"])
                self.assertEqual(seg["text"], "second")

                return {"status": "ok"}

            mock_create.side_effect = create_side_effect

            # Act
            result = process_single_clip(clip_index, clip, url, transcription, segment_starts)

            # Assert
            self.assertEqual(result, {"status": "ok"})
            mock_download.assert_called_once()
            mock_create.assert_called_once()


def cleanup_temp(temp_dir: str = None):
    """Remove all temporary files after processing."""
    temp_path = Path(temp_dir) if temp_dir else TEMP_DIR
    if temp_path.exists():
        file_count = sum(1 for f in temp_path.iterdir() if f.is_file())
        if file_count > 0:
            for f in temp_path.iterdir():
                if f.is_file():
                    f.unlink()
            print(f"[CLEANUP] Cleaned up {file_count} temp files")


def process_video(url: str, dry_run: bool = False) -> list:
    """
    Main pipeline: Process YouTube video into viral clips
    
    Args:
        url: YouTube video URL
        dry_run: If True, analyze only (no video download/processing)
        
    Returns:
        List of output file paths
    """
    print("\n" + "="*60)
    print("[AUTO-CLIP BOT V2] Pipeline Starting")
    if dry_run:
        print("   [DRY RUN] Analyze only, no processing")
    print("="*60 + "\n")
    
    # Step 0: Validate dependencies
    validate_dependencies()
    
    # === PIPELINE STEPS (with progress bar) ===
    steps = [
        "[INFO] Get video info",
        "[DL] Download audio",
        "[AI] Transcribe (Whisper)",
        "[AI] AI clip analysis",
        "[CLIP] Process clips",
    ]
    
    progress = tqdm(steps, desc="Pipeline", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]")
    
    # Step 1: Get video info
    progress.set_description("[INFO] Getting video info")
    video_info = get_video_info(url)
    print(f"\n   Title: {video_info['title']}")
    print(f"   Duration: {video_info['duration']}s ({video_info['duration']//60}m {video_info['duration']%60}s)")
    progress.update(1)
    
    # Step 2: Download audio only (fast & lightweight)
    progress.set_description("[DL] Downloading audio")
    audio_path = download_audio_only(url, str(DOWNLOADS_DIR))
    progress.update(1)
    
    # Step 3: Transcribe audio
    progress.set_description("[AI] Transcribing audio")
    transcription = transcribe_audio(audio_path)
    seg_count = len(transcription.get("segments", []))
    text_len = len(transcription.get("text", ""))
    print(f"\n   [TEXT] Transcribed: {seg_count} segments, {text_len} chars")
    progress.update(1)
    
    # Step 4: Analyze content and find viral clips
    progress.set_description("[AI] Analyzing content")
    clips = analyze_content_for_clips(transcription, video_info)
    progress.update(1)
    
    if not clips:
        progress.close()
        print("! No suitable clips found!")
        return []
    
    # Print clip summary
    print(f"\n   Found {len(clips)} potential clips:")
    for i, clip in enumerate(clips, 1):
        duration = clip['end'] - clip['start']
        print(f"   {i}. [{clip['start']:.0f}s - {clip['end']:.0f}s] ({duration:.0f}s) {clip.get('caption_title', '')}")
        print(f"      Type: {clip.get('narrative_type', '-')} | Mood: {clip.get('mood', 'unknown')}")
        if clip.get('hook'):
            print(f"      [HOOK] Hook: \"{clip['hook'][:80]}\"")
        print(f"      [STORY] {clip.get('reason', '')[:80]}...")
    
    # Dry run stops here
    if dry_run:
        progress.close()
        print("\n" + "="*60)
        print("[DRY RUN] DRY RUN COMPLETE — Analysis done, no clips processed")
        print("="*60)
        print("\nRun without --dry-run to generate clips.")
        return []
    
    # Step 5: Process each clip
    progress.set_description("[CLIP] Processing clips")
    outputs = []
    
    # Use ThreadPoolExecutor for parallel processing
    # Recommended max_workers=3 to prevent stability issues
    max_workers = 3
    print(f"   [PARALLEL] Processing clips with {max_workers} threads...")
    
    temp_results = []
    segment_starts = [seg["start"] for seg in transcription.get("segments", [])]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_clip = {
            executor.submit(process_single_clip, i, clip, url, transcription, segment_starts): i
            for i, clip in enumerate(clips, 1)
        }
        
        clip_progress = tqdm(
            concurrent.futures.as_completed(future_to_clip),
            total=len(clips),
            desc="Clips",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
        )
        
        for future in clip_progress:
            i = future_to_clip[future]
            try:
                result = future.result()
                if result:
                    temp_results.append((i, result))
            except Exception as e:
                print(f"\n! Error getting result for clip {i}: {e}")
    
    # Sort results by clip number to maintain order
    temp_results.sort(key=lambda x: x[0])
    outputs = [r[1] for r in temp_results]
    progress.update(1)
    progress.close()
    
    # Cleanup temp files
    cleanup_temp()
    
    # Summary
    print("\n" + "="*60)
    print("[DONE] PROCESSING COMPLETE!")
    print("="*60)
    print(f"\n[DIR] Output directory: {OUTPUT_DIR}")
    print(f"[CLIP] Total clips created: {len(outputs)}")
    
    for i, output in enumerate(outputs, 1):
        print(f"\n   Clip {i}:")
        print(f"      [VIDEO] {Path(output['video']).name}")
        print(f"      [THUMB] {Path(output['thumbnail']).name}")
        print(f"      [TEXT] {Path(output['caption_file']).name}")
    
    return outputs


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Auto-Clip Bot V2 — Transform long videos into viral clips",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py https://www.youtube.com/watch?v=VIDEO_ID
    python main.py --url https://youtu.be/VIDEO_ID
    python main.py --url https://youtu.be/VIDEO_ID --dry-run
        """
    )
    
    parser.add_argument(
        "url",
        nargs="?",
        help="YouTube video URL"
    )
    parser.add_argument(
        "--url", "-u",
        dest="url_flag",
        help="YouTube video URL (alternative)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Analyze only, don't process clips"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed stack traces on error"
    )
    
    args = parser.parse_args()
    
    # Get URL from either positional or flag argument
    url = args.url or args.url_flag
    
    if not url:
        parser.print_help()
        print("\n[ERROR] Error: Please provide a YouTube URL")
        sys.exit(1)
    
    # Validate URL looks like YouTube
    if "youtube.com" not in url and "youtu.be" not in url:
        print("[WARN] Warning: URL doesn't look like a YouTube link")
    
    try:
        outputs = process_video(url, dry_run=args.dry_run)
        
        if outputs:
            print("\n[SUCCESS] Success! Your clips are ready for upload.")
            print("[DIR] Check the output folder:", OUTPUT_DIR)
        elif not args.dry_run:
            print("\n[INFO] No clips were created. Try a different video.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n[STOP] Process cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
