## 2026-02-12 - SSRF via yt-dlp
**Vulnerability:** yt-dlp can access internal network services (SSRF) via generic HTTP extractor. The application accepted any URL, exposing internal services to potential attackers.
**Learning:** CLI tools like yt-dlp are powerful and can be used for SSRF if input is not validated.
**Prevention:** Strictly validate input URLs to expected domains (YouTube) and schemes (http/https) before passing to yt-dlp.

## 2026-02-12 - SSRF/Arbitrary File Read via FFmpeg/FFprobe
**Vulnerability:** FFmpeg and FFprobe CLI tools are vulnerable to SSRF, arbitrary file reads, and protocol injection when handling untrusted user input paths. They do not support `--` to delimit arguments, making them susceptible to these attacks.
**Learning:** Even well-established CLI tools like FFmpeg can introduce critical security risks if input paths are not properly sanitized and restricted.
**Prevention:** Always prepend `file:` to input (`-i`) and output file paths when invoking FFmpeg or FFprobe via `subprocess` to force the tools to treat the path strictly as a local file, preventing protocol injection (e.g., `http://`, `concat:`).
