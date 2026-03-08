## 2026-02-12 - SSRF via yt-dlp
**Vulnerability:** yt-dlp can access internal network services (SSRF) via generic HTTP extractor. The application accepted any URL, exposing internal services to potential attackers.
**Learning:** CLI tools like yt-dlp are powerful and can be used for SSRF if input is not validated.
**Prevention:** Strictly validate input URLs to expected domains (YouTube) and schemes (http/https) before passing to yt-dlp.

## 2025-05-18 - Subtitle Injection via ASS Tags
**Vulnerability:** The application constructs Advanced SubStation Alpha (.ass) subtitle files from user-controlled transcript text without sanitization. Attackers can inject ASS tags (`{`, `}`, `\`) to execute arbitrary formatting, obscuring content, or potentially exploiting vulnerabilities in media players parsing these malicious tags.
**Learning:** Automatically generated subtitle files, particularly rich formats like .ass which support complex styling and overriding commands, are susceptible to injection attacks if the text originates from external or untrusted sources (e.g. speech-to-text outputs or LLM generation).
**Prevention:** Always sanitize input text bound for ASS subtitle files by escaping or replacing sensitive characters (`{`, `}`, `\`). Full-width equivalents (`｛`, `｝`, `＼`) offer a safe method to preserve readability while neutering tag functionality.

## 2026-02-12 - SSRF/Arbitrary File Read via FFmpeg/FFprobe
**Vulnerability:** FFmpeg and FFprobe CLI tools are vulnerable to SSRF, arbitrary file reads, and protocol injection when handling untrusted user input paths. They do not support `--` to delimit arguments, making them susceptible to these attacks.
**Learning:** Even well-established CLI tools like FFmpeg can introduce critical security risks if input paths are not properly sanitized and restricted.
**Prevention:** Always prepend `file:` to input (`-i`) and output file paths when invoking FFmpeg or FFprobe via `subprocess` to force the tools to treat the path strictly as a local file, preventing protocol injection (e.g., `http://`, `concat:`).

## 2026-02-12 - Missing file: prefix for output paths in FFmpeg
**Vulnerability:** The processor script failed to prefix output file paths and secondary input paths with `file:` in multiple FFmpeg subprocess calls. While input paths were generally prefixed, missing it on outputs still exposes the script to protocol injection vulnerabilities, allowing arbitrary file writes, SSRF, or other exploits depending on the provided paths.
**Learning:** All file paths passed to FFmpeg and FFprobe (both `-i` inputs and positional outputs) must explicitly include the `file:` prefix when invoked via `subprocess`, due to FFmpeg's lack of a `--` argument delimiter.
**Prevention:** Systematically apply `file:` to every dynamic path used in FFmpeg/FFprobe subprocess commands.

## 2026-02-12 - Process Hang / Denial of Service (DoS) via subprocess
**Vulnerability:** Multiple `subprocess.run` calls executing external processes (like `ffmpeg` or `ffprobe`) lacked an explicit `timeout` parameter. Malformed inputs, unexpected system conditions, or intentionally crafted files could cause these underlying processes to hang indefinitely, leading to resource exhaustion and a Denial of Service (DoS) for the application.
**Learning:** By default, `subprocess.run` waits indefinitely for the process to complete. In production environments, especially when processing external or user-provided files, external processes can fail in ways that cause them to hang.
**Prevention:** Always include a reasonable explicit `timeout` parameter when calling `subprocess.run` to ensure the application fails securely (with a `subprocess.TimeoutExpired` exception) instead of hanging indefinitely.
