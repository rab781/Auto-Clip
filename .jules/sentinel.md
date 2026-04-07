## 2026-02-12 - SSRF via yt-dlp
**Vulnerability:** yt-dlp can access internal network services (SSRF) via generic HTTP extractor. The application accepted any URL, exposing internal services to potential attackers.
**Learning:** CLI tools like yt-dlp are powerful and can be used for SSRF if input is not validated.
**Prevention:** Strictly validate input URLs to expected domains (YouTube) and schemes (http/https) before passing to yt-dlp.

## 2025-05-18 - SSRF via DNS Rebinding/Domain Spoofing
**Vulnerability:** The application relied on validating the parsed URL `netloc` against a strict allow-list. This is fragile because `netloc` can include userinfo and ports (for example, `youtube.com:443` or `youtube.com@attacker.tld`), and raw comparisons can miss hostname normalization issues.
**Learning:** Allow-list checks should be performed on the parsed and normalized `hostname`, not raw `netloc`. URL components such as credentials, ports, casing, and trailing-dot forms can make `netloc`-based validation inaccurate and unsafe.
**Prevention:** Parse the URL, extract and normalize `hostname`, and compare that normalized hostname against the explicit allow-list of supported YouTube domains before allowing the request to proceed.

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

## 2026-03-15 - API Key Leakage via Error Messages
**Vulnerability:** The application was catching API HTTP errors (like 500s or 401s) and directly formatting the external API's response payload (`response.text`) into its own exception or log messages. If the external API echoes back the invalid/provided authorization token in its error body, the application will leak this sensitive key into internal logs, user interfaces, or stack traces.
**Learning:** External API error responses are fundamentally untrusted and can inadvertently reflect back sensitive request data (like API keys or tokens). Treating `response.text` as safe for logging or exception bubbling creates an information disclosure vulnerability.
**Prevention:** Always sanitize exception and error messages originating from external sources before logging them or bubbling them up. Implement a centralized redaction function that strips configured secrets (e.g., `CHUTES_API_KEY`) from strings, replacing them with placeholders like `[REDACTED]`.

## 2026-03-24 - Unauthorized Local File Access via Permissive Directory Creation
**Vulnerability:** When initializing directories for sensitive temporary files (`DOWNLOADS_DIR`, `TEMP_DIR`), the app relied on default permissions `mkdir(parents=True, exist_ok=True)`, which allowed any local user to read API payloads or downloaded media.
**Learning:** Failing to explicitly enforce strict file permissions during initialization leaves potentially sensitive temporary files exposed to local users.
**Prevention:** Explicitly apply strict directory permissions (e.g., `mode=0o700`) during `mkdir()` to prevent unauthorized local read/write access.
## 2025-02-18 - Path Traversal & Protocol/Argument Injection Prevention in FFmpeg
**Vulnerability:** External CLI tools like `ffmpeg` or `ffprobe` (which do not support `--` as a delimiter) are susceptible to SSRF, path traversal, or argument injection (where a path starting with a hyphen `-` could be misinterpreted as a flag).
**Learning:** Prefixing a file path simply with `file:` in `subprocess.run` may not sufficiently prevent argument injection if the path evaluates to a relative path containing a hyphen or allows directory traversal via relative dots.
**Prevention:** All user-controlled file paths (inputs and outputs) passed to external tools without a dedicated path delimiter must be converted to absolute paths using `os.path.abspath()` and prepended with the `file:` protocol (e.g., `f'file:{os.path.abspath(path)}'`).

## 2024-05-26 - DoS via Log Flooding and Information Exposure
**Vulnerability:** Exception payloads returned by external tools (like `yt-dlp` or API calls) were thrown or logged without length constraints. Attackers could manipulate input to cause these dependencies to fail and return massive error payloads (e.g., large HTML documents), resulting in log flooding, resource exhaustion, or accidental exposure of massive amounts of internal tool state.
**Learning:** External error payloads are completely untrusted inputs. Taking large error responses verbatim exposes an application to Information Exposure and Denial of Service (DoS) attacks via memory or log exhaustion.
**Prevention:** Always string-slice and truncate raw error messages (e.g., `str(e)[:500]`) before raising them internally or logging them.