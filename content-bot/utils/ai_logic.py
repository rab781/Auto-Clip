# ai_logic.py - AI Processing Logic
"""
Modul untuk AI processing:
- Speech-to-Text menggunakan Whisper (Chutes.ai)
- Clip selection menggunakan LLM (Chutes.ai)
- BGM recommendation based on content mood
"""
import requests
import json
import re
import subprocess
import sys
import time
import functools
import concurrent.futures
sys.path.append(str(__file__).rsplit('\\', 2)[0])

from config import CHUTES_API_KEY, CHUTES_BASE_URL, WHISPER_MODEL, LLM_MODEL, VIDEO_SETTINGS


def validate_dependencies():
    """Validate that FFmpeg and ffprobe are available on the system."""
    for tool in ["ffmpeg", "ffprobe"]:
        try:
            result = subprocess.run(
                [tool, "-version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                raise FileNotFoundError
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print(f"❌ FATAL: '{tool}' tidak ditemukan di PATH!")
            print(f"   Install FFmpeg: https://ffmpeg.org/download.html")
            print(f"   Pastikan '{tool}' ada di system PATH.")
            sys.exit(1)
    print("✅ FFmpeg & ffprobe ready")


def api_retry(max_retries: int = 3, base_delay: int = 5):
    """Decorator untuk retry API calls dengan exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.Timeout as e:
                    last_error = e
                    wait = base_delay * (2 ** attempt)
                    print(f"   ⏰ Timeout (attempt {attempt+1}/{max_retries}), retry in {wait}s...")
                    time.sleep(wait)
                except requests.exceptions.ConnectionError as e:
                    last_error = e
                    wait = base_delay * (2 ** attempt)
                    print(f"   🔌 Connection error (attempt {attempt+1}/{max_retries}), retry in {wait}s...")
                    time.sleep(wait)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait = base_delay * (attempt + 1)
                        print(f"   ⚠️ Error: {str(e)[:80]} (attempt {attempt+1}/{max_retries}), retry in {wait}s...")
                        time.sleep(wait)
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator


def transcribe_audio(audio_path: str, max_retries: int = 3, chunk_duration: int = 300) -> dict:
    """
    Transcribe audio menggunakan Chutes Whisper API dengan audio splitting
    untuk menghindari 504 timeout pada file besar.
    
    Args:
        audio_path: Path ke file audio
        max_retries: Jumlah maksimal retry per chunk
        chunk_duration: Durasi per chunk dalam detik (default: 300 = 5 menit)
        
    Returns:
        Dictionary dengan transcript dan segments (timestamps)
    """
    import os
    import time
    import base64
    import subprocess
    from pathlib import Path
    
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"🎤 Transcribing audio: {audio_path}")
    print(f"   File size: {file_size_mb:.1f} MB")
    
    # Get audio duration using ffprobe
    duration = _get_audio_duration(audio_path)
    print(f"   Duration: {duration:.0f}s ({duration/60:.1f} menit)")
    
    # Determine if we need to split
    if duration <= chunk_duration:
        # Small file, process directly
        print(f"   ✅ File kecil, proses langsung tanpa split")
        return _transcribe_chunk(audio_path, 0, max_retries)
    
    # Split audio into chunks
    num_chunks = int(duration // chunk_duration) + (1 if duration % chunk_duration > 0 else 0)
    print(f"   📦 Splitting audio into {num_chunks} chunks ({chunk_duration}s each)...")
    
    temp_dir = Path(audio_path).parent / "temp_chunks"
    temp_dir.mkdir(exist_ok=True)
    
    all_segments = []
    full_text = ""
    
    def process_chunk_task(task_args):
        """Helper to process a single chunk in a thread."""
        idx, start_ts, end_ts = task_args
        chunk_file = temp_dir / f"chunk_{idx:03d}.mp3"
        label = f"Chunk {idx+1}/{num_chunks}"
        
        try:
            print(f"\n   📍 Processing {label} [{start_ts:.0f}s - {end_ts:.0f}s]...")
            
            # Extract chunk using ffmpeg
            _extract_audio_chunk(audio_path, str(chunk_file), start_ts, end_ts)
            
            # Transcribe chunk
            # Note: _transcribe_chunk internally does retries
            res = _transcribe_chunk(str(chunk_file), start_ts, max_retries, chunk_label=label)
            
            # Clean up chunk file
            chunk_file.unlink(missing_ok=True)
            return (idx, start_ts, res)
            
        except Exception as err:
            print(f"   ⚠️ {label} failed: {err}")
            chunk_file.unlink(missing_ok=True)
            return (idx, start_ts, None)

    # Prepare tasks
    tasks = []
    for i in range(num_chunks):
        start_time = i * chunk_duration
        end_time = min((i + 1) * chunk_duration, duration)
        tasks.append((i, start_time, end_time))

    results = []
    # Use ThreadPoolExecutor for parallel processing
    # Limit max_workers to 3 to avoid hitting API rate limits or overwhelming the system
    max_workers = min(3, num_chunks)
    print(f"   ⚡ Parallel processing with {max_workers} threads...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(process_chunk_task, t): t for t in tasks}

        for future in concurrent.futures.as_completed(future_to_chunk):
            try:
                idx, start_ts, res = future.result()
                if res:
                    results.append((idx, start_ts, res))
            except Exception as exc:
                print(f"   ❌ task generated an exception: {exc}")

    # Sort results by index to maintain order
    results.sort(key=lambda x: x[0])

    # Merge results
    for idx, start_ts, result in results:
        if "segments" in result:
            for seg in result["segments"]:
                seg["start"] += start_ts
                seg["end"] += start_ts
                all_segments.append(seg)

        full_text += " " + result.get("text", "")
    
    # Clean up temp directory
    try:
        temp_dir.rmdir()
    except:
        pass
    
    print(f"\n✅ Transcription complete: {len(full_text)} characters, {len(all_segments)} segments")
    
    return {
        "text": full_text.strip(),
        "segments": all_segments
    }


def _get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe"""
    import subprocess
    
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        return float(result.stdout.strip())
    except:
        return 600.0  # Default fallback 10 menit


def _extract_audio_chunk(audio_path: str, output_path: str, start: float, end: float):
    """Extract a chunk of audio using ffmpeg"""
    import subprocess
    
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", str(audio_path),
        "-t", str(duration),
        "-acodec", "libmp3lame",
        "-q:a", "4",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr[:200]}")


def _transcribe_chunk(audio_path: str, time_offset: float, max_retries: int = 3, chunk_label: str = "") -> dict:
    """Transcribe a single audio chunk"""
    import os
    import time
    import base64
    
    headers = {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Read and encode audio to base64
    with open(audio_path, "rb") as audio_file:
        audio_b64 = base64.b64encode(audio_file.read()).decode("utf-8")
    
    body = {
        "language": "id",
        "audio_b64": audio_b64
    }
    
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    timeout = max(180, int(file_size_mb * 30) + 60)
    
    prefix = f"      [{chunk_label}]" if chunk_label else "      "

    for attempt in range(max_retries):
        try:
            print(f"{prefix} 📤 Uploading (attempt {attempt + 1}/{max_retries})...")
            
            response = requests.post(
                "https://chutes-whisper-large-v3.chutes.ai/transcribe",
                headers=headers,
                json=body,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Normalize response format
                if isinstance(result, list):
                    full_text = " ".join([seg.get("text", "") for seg in result if isinstance(seg, dict)])
                    segments = []
                    for seg in result:
                        if isinstance(seg, dict):
                            segments.append({
                                "start": seg.get("start", 0),
                                "end": seg.get("end", 0),
                                "text": seg.get("text", "")
                            })
                    result = {"text": full_text, "segments": segments}
                elif isinstance(result, dict):
                    if "text" not in result and "transcription" in result:
                        result["text"] = result["transcription"]
                    if "segments" not in result:
                        result["segments"] = [{"start": 0, "end": 60, "text": result.get("text", "")}]
                
                print(f"{prefix} ✅ Transcribed: {len(result.get('text', ''))} chars")
                return result
            elif response.status_code == 504:
                print(f"{prefix} ⏰ 504 Timeout on attempt {attempt + 1}")
            else:
                print(f"{prefix} ⚠️ API status {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print(f"{prefix} ⏰ Request timeout on attempt {attempt + 1}")
        except Exception as e:
            print(f"{prefix} ❌ Error on attempt {attempt + 1}: {str(e)[:80]}")
        
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 20
            print(f"{prefix} ⏳ Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    raise Exception(f"Failed to transcribe chunk after {max_retries} attempts")


def translate_segments(segments: list, target_lang: str = "Indonesian") -> list:
    """
    Batch translate subtitle segments ke Bahasa Indonesia.
    Translate 20 segments sekaligus untuk hemat API calls.
    
    Args:
        segments: List of whisper segments [{start, end, text}, ...]
        target_lang: Target language for translation
        
    Returns:
        List of translated segments (same structure, text ditranslate)
    """
    if not segments:
        return segments
    
    headers = {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json",
    }
    
    translated = []
    batch_size = 20  # Translate 20 segments at once
    total_batches = (len(segments) + batch_size - 1) // batch_size
    
    print(f"🌐 Translating {len(segments)} segments to {target_lang} ({total_batches} batches)...")
    
    for batch_idx in range(0, len(segments), batch_size):
        batch = segments[batch_idx:batch_idx + batch_size]
        batch_num = (batch_idx // batch_size) + 1
        
        # Build numbered text for batch translation
        numbered_texts = []
        for i, seg in enumerate(batch):
            text = seg["text"].strip()
            if text:
                numbered_texts.append(f"{i+1}. {text}")
        
        if not numbered_texts:
            translated.extend(batch)
            continue
        
        batch_text = "\n".join(numbered_texts)
        
        prompt = f"""Terjemahkan SEMUA kalimat berikut ke Bahasa Indonesia.
PENTING: 
- Pertahankan nomor urut di awal setiap baris
- Terjemahkan dengan natural, bukan kaku
- Jika sudah dalam Bahasa Indonesia, biarkan apa adanya
- JANGAN tambahkan penjelasan apapun

{batch_text}"""
        
        data = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": "Kamu adalah penerjemah profesional. Tugasmu HANYA menerjemahkan teks yang diberikan ke Bahasa Indonesia. Output HANYA terjemahan dengan nomor urut, tanpa penjelasan."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1500,
        }
        
        try:
            print(f"   📝 Batch {batch_num}/{total_batches}...")
            response = requests.post(
                f"{CHUTES_BASE_URL}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result["choices"][0]["message"]["content"].strip()
                
                # Parse numbered translations back
                translations = {}
                for line in translated_text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    # Match "1. translated text" format
                    match = re.match(r'^(\d+)\.\s*(.+)$', line)
                    if match:
                        idx = int(match.group(1)) - 1
                        translations[idx] = match.group(2).strip()
                
                # Apply translations to batch
                for i, seg in enumerate(batch):
                    new_seg = seg.copy()
                    if i in translations:
                        new_seg["text"] = translations[i]
                    translated.append(new_seg)
                
                translated_count = len(translations)
                print(f"      ✅ {translated_count}/{len(batch)} segments translated")
            else:
                print(f"      ⚠️ Translation API error ({response.status_code}), using original text")
                translated.extend(batch)
                
        except Exception as e:
            print(f"      ❌ Translation error: {str(e)[:80]}, using original text")
            translated.extend(batch)
    
    print(f"✅ Translation complete: {len(translated)} segments")
    return translated


def analyze_content_for_clips(transcription: dict, video_info: dict = None) -> list:
    """
    Analyze transcript dan pilih bagian paling menarik untuk dijadikan clips
    
    Args:
        transcription: Output dari transcribe_audio()
        video_info: Optional video metadata
        
    Returns:
        List of clip recommendations: [{start, end, reason, caption_title, mood}]
    """
    headers = {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Format transcript dengan timestamps
    segments_text = ""
    if "segments" in transcription:
        for seg in transcription["segments"]:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "")
            segments_text += f"[{start:.1f}s - {end:.1f}s]: {text}\n"
    else:
        segments_text = transcription.get("text", "")
    
    video_context = ""
    if video_info:
        video_context = f"Video title: {video_info.get('title', 'Unknown')}\n"
    
    prompt = f"""Kamu adalah EDITOR VIDEO VIRAL PROFESIONAL level Hollywood untuk TikTok/Shorts/Reels.
Kamu memahami NARRATIVE ARC (struktur cerita) dan tahu cara membuat penonton KETAGIHAN.

{video_context}
Durasi total video: {video_info.get('duration', 'unknown')} detik

Berikut adalah transkrip video dengan timestamp:
{segments_text}

=== TUGAS UTAMA ===
Analisis transkrip ini secara SEMANTIK dan identifikasi 2-5 CHAPTER/SEGMENT yang memiliki cerita lengkap.

=== ATURAN CLIPPING (SANGAT PENTING) ===

1. NARRATIVE ARC - Setiap clip HARUS punya struktur cerita:
   - HOOK (5-10 detik pertama): Mulai dari momen yang bikin PENASARAN.
     Contoh: "Detak jantung pasien tiba-tiba 200!", "Dokternya langsung panik..."
   - BUILDUP: Bangun konteks dan tension. Jangan skip bagian ini!
   - CLIMAX/PAYOFF: Puncak cerita yang satisfying.
   
2. HOOK DETECTION - Cari momen-momen yang bisa jadi opening:
   - Pertanyaan yang bikin penasaran
   - Momen shocking/unexpected
   - Statement kontroversial
   - Reaksi emosional kuat
   - Plot twist atau reveal

3. DURASI: Setiap clip {VIDEO_SETTINGS['min_clip_duration']}-{VIDEO_SETTINGS['max_clip_duration']} detik
   - Clip BOLEH panjang (2-5 menit) kalau ceritanya memang butuh
   - Jangan potong cerita di tengah! Pastikan ada CONCLUSION
   - Lebih baik clip panjang tapi cerita lengkap daripada pendek tapi gantung
   
4. SEMANTIC CHAPTER: Pahami TOPIK yang dibahas, jangan potong mekanis per waktu.
   - Identifikasi pergantian topik secara natural
   - Setiap clip = 1 cerita/topik lengkap
   
5. MOOD untuk BGM: "energetic", "emotional", "funny", "dramatic", "chill"

=== CONTOH HOOK YANG BAGUS ===
Video tentang dokter IGD:
❌ BURUK: Mulai dari "Jadi hari ini saya ceritakan tentang..." (boring, skip-able)
✅ BAGUS: Mulai dari "Detak jantung istri saya tiba-tiba 200! Dokternya langsung..." (penasaran!)

=== FORMAT OUTPUT ===
PENTING: SEMUA OUTPUT HARUS DALAM BAHASA INDONESIA!

OUTPUT dalam format JSON VALID (tanpa markdown code blocks):
[
  {{
    "start": <detik_mulai>,
    "end": <detik_selesai>,
    "hook": "<kalimat pembuka yang bikin PENASARAN, dalam BAHASA INDONESIA>",
    "reason": "<jelaskan narrative arc: hook-nya apa, buildup-nya bagaimana, climax-nya di mana>",
    "caption_title": "<judul singkat dalam BAHASA INDONESIA yang clickbait tapi jujur>",
    "mood": "<mood untuk BGM>",
    "narrative_type": "<tipe: story/reaction/education/controversy/motivation>"
  }}
]

HANYA OUTPUT JSON, tanpa penjelasan tambahan."""

    data = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "Kamu adalah AI editor video yang memahami storytelling dan narrative arc. Tugasmu adalah menemukan cerita-cerita menarik di dalam video panjang dan memotongnya menjadi clip pendek yang viral. Kamu SELALU menjawab dalam format JSON valid."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 2000,
    }
    
    print("🧠 Analyzing content for viral clips...")
    response = requests.post(
        f"{CHUTES_BASE_URL}/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"LLM API error: {response.text}")
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Parse JSON from response
    clips = _parse_clips_json(content)
    
    # Validate clips
    validated_clips = []
    for clip in clips:
        duration = clip["end"] - clip["start"]
        if VIDEO_SETTINGS['min_clip_duration'] <= duration <= VIDEO_SETTINGS['max_clip_duration']:
            validated_clips.append(clip)
        elif duration < VIDEO_SETTINGS['min_clip_duration']:
            print(f"⚠️ Clip terlalu pendek ({duration:.0f}s < {VIDEO_SETTINGS['min_clip_duration']}s): {clip.get('caption_title', 'unknown')}")
        elif duration > VIDEO_SETTINGS['max_clip_duration']:
            # Split terlalu panjang? Tetap terima tapi warning
            print(f"⚠️ Clip agak panjang ({duration:.0f}s), tetap diproses: {clip.get('caption_title', 'unknown')}")
            validated_clips.append(clip)
    
    # Sort by start time
    validated_clips.sort(key=lambda x: x["start"])
    
    print(f"✅ Found {len(validated_clips)} valid clips")
    for i, clip in enumerate(validated_clips, 1):
        duration = clip['end'] - clip['start']
        hook = clip.get('hook', '')[:60]
        print(f"   {i}. [{clip['start']:.0f}s-{clip['end']:.0f}s] ({duration:.0f}s) {clip.get('caption_title', '')}")
        if hook:
            print(f"      🪝 Hook: \"{hook}...\"")
    return validated_clips


def generate_clip_caption(clip_info: dict, transcript_segment: str) -> str:
    """
    Generate engaging caption/hook text untuk clip
    
    Args:
        clip_info: Clip metadata (dari analyze_content_for_clips)
        transcript_segment: Transcript text untuk segment ini
        
    Returns:
        Caption text yang engaging
    """
    headers = {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json",
    }
    
    hook_text = clip_info.get('hook', '')
    narrative_type = clip_info.get('narrative_type', 'story')
    
    prompt = f"""Buat caption untuk posting video pendek ini di TikTok/Instagram Reels.
SEMUA HARUS DALAM BAHASA INDONESIA.

Judul: {clip_info.get('caption_title', '')}
Hook video: {hook_text}
Tipe konten: {narrative_type}
Alasan menarik: {clip_info.get('reason', '')}
Isi transkrip: {transcript_segment[:500]}

FORMAT CAPTION:
1. Baris pertama: HOOK kalimat yang bikin stop scrolling (boleh pakai hook video di atas sebagai inspirasi)
2. Baris kedua: 1 kalimat penjelasan singkat yang bikin penasaran
3. Baris ketiga: CTA (Call to Action) seperti "Follow untuk Part 2!" atau "Save biar ga hilang!"
4. Baris keempat: 3-5 hashtag relevan dalam Bahasa Indonesia

GAYA: Casual, Gen-Z friendly Indonesia. Boleh pakai emoji tapi jangan berlebihan.

OUTPUT langsung caption-nya saja, tanpa label atau penjelasan."""

    data = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 150,
    }
    
    response = requests.post(
        f"{CHUTES_BASE_URL}/chat/completions",
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        return clip_info.get('caption_title', 'Check this out! 🔥')
    
    result = response.json()
    return result["choices"][0]["message"]["content"].strip()


def _parse_clips_json(content: str) -> list:
    """Parse JSON from LLM response, handling various formats"""
    # Try direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON array from response
    json_match = re.search(r'\[[\s\S]*\]', content)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Fallback: empty list
    print("⚠️ Could not parse clips JSON, returning empty list")
    return []


if __name__ == "__main__":
    # Quick test dengan dummy data
    test_transcription = {
        "text": "Ini adalah contoh transkrip untuk testing",
        "segments": [
            {"start": 0, "end": 30, "text": "Bagian pertama yang menarik"},
            {"start": 30, "end": 60, "text": "Bagian kedua yang viral"},
        ]
    }
    
    print("Testing analyze_content_for_clips...")
    # clips = analyze_content_for_clips(test_transcription)
    # print(clips)