## 2026-02-12 - SSRF via yt-dlp
**Vulnerability:** yt-dlp can access internal network services (SSRF) via generic HTTP extractor. The application accepted any URL, exposing internal services to potential attackers.
**Learning:** CLI tools like yt-dlp are powerful and can be used for SSRF if input is not validated.
**Prevention:** Strictly validate input URLs to expected domains (YouTube) and schemes (http/https) before passing to yt-dlp.

## 2026-03-01 - ASS Injection in Subtitles
**Vulnerability:** User-controlled text in subtitles was not sanitized, allowing injection of Advanced Substation Alpha (ASS) override tags (e.g., `{\b1}`), which could alter video rendering.
**Learning:** Subtitle formats like ASS have complex syntax that can be abused if text is concatenated directly without escaping.
**Prevention:** Sanitize all user input by replacing control characters (`{`, `}`, `\`) with safe alternatives (e.g., full-width characters) before embedding in subtitle files.
