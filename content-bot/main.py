# main.py - Auto-Clip Pipeline Orchestrator
"""
Auto-Clip Bot - Main Entry Point
Bot otomatis untuk mengubah video YouTube panjang menjadi klip pendek viral

Usage:
    python main.py <youtube_url>
    python main.py --url <youtube_url>
"""
import sys
import argparse
from pathlib import Path

from config import DOWNLOADS_DIR, TEMP_DIR, OUTPUT_DIR
from utils import (
    download_audio_only,
    download_video_segment,
    get_video_info,
    transcribe_audio,
    analyze_content_for_clips,
    generate_clip_caption,
    translate_segments,
    create_final_clip,
)


def process_video(url: str) -> list:
    """
    Main pipeline: Process YouTube video into viral clips
    
    Args:
        url: YouTube video URL
        
    Returns:
        List of output file paths
    """
    print("\n" + "="*60)
    print("🚀 AUTO-CLIP BOT - Starting Pipeline")
    print("="*60 + "\n")
    
    # Step 1: Get video info
    print("📋 Step 1: Getting video info...")
    video_info = get_video_info(url)
    print(f"   Title: {video_info['title']}")
    print(f"   Duration: {video_info['duration']}s ({video_info['duration']//60}m {video_info['duration']%60}s)")
    
    # Step 2: Download audio only (fast & lightweight)
    print("\n📥 Step 2: Downloading audio only...")
    audio_path = download_audio_only(url, str(DOWNLOADS_DIR))
    
    # Step 3: Transcribe audio
    print("\n🎤 Step 3: Transcribing audio with Whisper...")
    transcription = transcribe_audio(audio_path)
    
    # Step 4: Analyze content and find viral clips
    print("\n🧠 Step 4: Analyzing content for viral clips...")
    clips = analyze_content_for_clips(transcription, video_info)
    
    if not clips:
        print("❌ No suitable clips found!")
        return []
    
    print(f"   Found {len(clips)} potential clips:")
    for i, clip in enumerate(clips, 1):
        duration = clip['end'] - clip['start']
        print(f"   {i}. [{clip['start']:.0f}s - {clip['end']:.0f}s] ({duration:.0f}s) {clip['caption_title']}")
        print(f"      Type: {clip.get('narrative_type', '-')} | Mood: {clip.get('mood', 'unknown')}")
        if clip.get('hook'):
            print(f"      🪝 Hook: \"{clip['hook'][:80]}\"")
        print(f"      📖 {clip['reason'][:80]}...")
    
    # Step 5: Process each clip
    print("\n🎬 Step 5: Processing clips...")
    outputs = []
    
    for i, clip in enumerate(clips, 1):
        print(f"\n{'='*50}")
        print(f"Processing Clip {i}/{len(clips)}")
        print(f"{'='*50}")
        
        # Download video segment
        segment_path = TEMP_DIR / f"segment_{i}.mp4"
        try:
            download_video_segment(url, clip["start"], clip["end"], str(segment_path))
        except Exception as e:
            print(f"⚠️ Failed to download segment: {e}")
            continue
        
        # Extract relevant transcript segments for this clip
        clip_segments = []
        if "segments" in transcription:
            for seg in transcription["segments"]:
                # Check if segment overlaps with clip timeframe
                if seg["start"] >= clip["start"] and seg["end"] <= clip["end"]:
                    # Adjust timestamps relative to clip start
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
            print(f"⚠️ Caption generation failed: {e}")
            clip["enhanced_caption"] = clip.get("caption_title", "")
        
        # Translate segments to Indonesian
        if clip_segments:
            print(f"\n🌐 Translating subtitle segments to Indonesian...")
            try:
                clip_segments = translate_segments(clip_segments)
            except Exception as e:
                print(f"⚠️ Translation failed, using original text: {e}")
        
        # Create final clip
        try:
            result = create_final_clip(
                video_segment_path=str(segment_path),
                clip_info=clip,
                segments=clip_segments,
                clip_number=i,
                output_dir=str(OUTPUT_DIR)
            )
            outputs.append(result)
        except Exception as e:
            print(f"❌ Failed to process clip {i}: {e}")
            continue
    
    # Summary
    print("\n" + "="*60)
    print("✅ PROCESSING COMPLETE!")
    print("="*60)
    print(f"\n📂 Output directory: {OUTPUT_DIR}")
    print(f"📹 Total clips created: {len(outputs)}")
    
    for i, output in enumerate(outputs, 1):
        print(f"\n   Clip {i}:")
        print(f"   └── 📹 {Path(output['video']).name}")
        print(f"   └── 🖼️ {Path(output['thumbnail']).name}")
        print(f"   └── 📝 {Path(output['caption_file']).name}")
    
    return outputs


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Auto-Clip Bot - Transform long videos into viral clips",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py https://www.youtube.com/watch?v=VIDEO_ID
    python main.py --url https://youtu.be/VIDEO_ID
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
    
    args = parser.parse_args()
    
    # Get URL from either positional or flag argument
    url = args.url or args.url_flag
    
    if not url:
        parser.print_help()
        print("\n❌ Error: Please provide a YouTube URL")
        sys.exit(1)
    
    # Validate URL looks like YouTube
    if "youtube.com" not in url and "youtu.be" not in url:
        print("⚠️ Warning: URL doesn't look like a YouTube link")
    
    try:
        outputs = process_video(url)
        
        if outputs:
            print("\n🎉 Success! Your clips are ready for upload.")
            print("📂 Check the output folder:", OUTPUT_DIR)
        else:
            print("\n😕 No clips were created. Try a different video.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Process cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
