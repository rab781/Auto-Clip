## 2026-02-12 - SSRF via yt-dlp
**Vulnerability:** yt-dlp can access internal network services (SSRF) via generic HTTP extractor. The application accepted any URL, exposing internal services to potential attackers.
**Learning:** CLI tools like yt-dlp are powerful and can be used for SSRF if input is not validated.
**Prevention:** Strictly validate input URLs to expected domains (YouTube) and schemes (http/https) before passing to yt-dlp.
## 2025-02-23 - [Critical] Prevent FFmpeg argument injection
**Vulnerability:** Untrusted file paths passed to `subprocess.run` involving `ffmpeg` or `ffprobe` without proper prefixing could be parsed as protocol options or arbitrary inputs (SSRF, arbitrary read). `ffmpeg` and `ffprobe` do not support standard `--` option delimiters.
**Learning:** Even if quotes are escaped, FFmpeg processes untrusted `-i` paths and output filenames dynamically. Attackers could potentially trigger unexpected protocol logic if a payload mimics a protocol handler or specific argument pattern.
**Prevention:** Always prepend `file:` to user-controlled or dynamically generated input/output file paths in FFmpeg and FFprobe calls. This explicitly forces FFmpeg to treat the input as a local file, ignoring any embedded protocol parsing. Ensure unit tests explicitly verify the presence of the `file:` prefix.
