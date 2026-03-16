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

## 2024-05-25 - Prevent DoS via Media Download Resource Exhaustion
**Vulnerability:** The application was downloading external media files (audio/video from YouTube) without enforcing file size or duration limits, creating a Denial of Service (DoS) vulnerability via resource exhaustion if an attacker provided a link to an oversized or excessively long video.
**Learning:** `yt-dlp` does not limit downloaded file sizes or durations by default. Applications must explicitly configure resource limits via `ydl_opts` to protect disk space, memory, and processing time, particularly when processing media autonomously.
**Prevention:** Always set `max_filesize` and use `match_filter` (e.g., `match_filter_func("duration <= limit")`) in the `yt-dlp` configuration (`ydl_opts`) when accepting URLs. Centralize these limits in a configuration file (like `DOWNLOAD_SETTINGS`) to ensure consistency across all download functions.

## 2026-02-12 - Prevent DoS via Hanging Network Connections in Media Downloads
**Vulnerability:** External media download utilities (like `yt-dlp`) lacked socket timeout configurations. An attacker could provide a URL pointing to a malicious server that accepts connections but sends data infinitely slowly (Slowloris-style attack) or hangs entirely, holding the server thread open and causing resource exhaustion (DoS).
**Learning:** Even with file size constraints (`max_filesize`), a hung connection can tie up application resources (threads, memory, file descriptors) indefinitely if no socket timeout is explicitly enforced.
**Prevention:** Always set network timeouts (e.g., `'socket_timeout': 60`) in download configurations (`ydl_opts`) for all external media metadata checks and downloads to ensure connections fail securely when stalled.

## 2026-03-14 - Incomplete Application of DoS Prevention in yt-dlp Utilities
**Vulnerability:** While `download_audio_only` was previously secured with a `match_filter` to reject videos exceeding `max_duration`, other `yt-dlp` functions (`download_video_segment` and `get_video_info`) lacked this filter. This inconsistency allowed an attacker to bypass the duration limits (e.g., pointing the bot to a continuous 24/7 live stream), causing resource exhaustion and potential DoS during segment extraction or massive metadata fetching.
**Learning:** Security controls applied to one utility function (like limiting file sizes or durations) are easily missed in similar or secondary utility functions within the same module, leading to partial protection.
**Prevention:** Ensure that global security constraints (such as `max_filesize`, `max_duration`, and `socket_timeout`) are systematically applied to *all* instances where an external dependency interacts with untrusted inputs.
## 2026-03-13 - Prevent Unauthenticated API Access (Fail Securely)
**Vulnerability:** The application executed API calls directly without initially validating if the required API key (`CHUTES_API_KEY`) was populated. This can lead to uncontrolled failures (stack traces, crashes) deep within API requests or expose the application to unauthenticated request behaviors.
**Learning:** Failing to validate the presence of required secrets early in the execution lifecycle compromises secure failure principles. An application should "fail fast and fail securely" rather than making predictably flawed unauthenticated network requests.
**Prevention:** Validate critical credentials early in the application flow (e.g., during dependency checking or initialization) and exit gracefully with clear, sanitized security messages if they are absent.

## 2026-03-24 - API Key Leakage via Unsanitized Error Messages
**Vulnerability:** The application was passing external API error responses (`response.text`) directly into printed logs and raised exceptions. If the API echoes back the request payload or includes the provided API key in its error message, this sensitive credential would be exposed in local logs or console output.
**Learning:** Error messages originating from external APIs must be treated as untrusted input. Directly bubbling them up without sanitization creates an Information Disclosure vulnerability, particularly concerning authorization tokens.
**Prevention:** Implement a helper function (e.g., `_sanitize_error_msg`) to dynamically scan and redact known sensitive values (like `CHUTES_API_KEY`) from external error payloads before they are logged, printed, or thrown in exceptions.
