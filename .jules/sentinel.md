## 2026-02-12 - SSRF via yt-dlp
**Vulnerability:** yt-dlp can access internal network services (SSRF) via generic HTTP extractor. The application accepted any URL, exposing internal services to potential attackers.
**Learning:** CLI tools like yt-dlp are powerful and can be used for SSRF if input is not validated.
**Prevention:** Strictly validate input URLs to expected domains (YouTube) and schemes (http/https) before passing to yt-dlp.

## 2025-05-18 - Subtitle Injection via ASS Tags
**Vulnerability:** The application constructs Advanced SubStation Alpha (.ass) subtitle files from user-controlled transcript text without sanitization. Attackers can inject ASS tags (`{`, `}`, `\`) to execute arbitrary formatting, obscuring content, or potentially exploiting vulnerabilities in media players parsing these malicious tags.
**Learning:** Automatically generated subtitle files, particularly rich formats like .ass which support complex styling and overriding commands, are susceptible to injection attacks if the text originates from external or untrusted sources (e.g. speech-to-text outputs or LLM generation).
**Prevention:** Always sanitize input text bound for ASS subtitle files by escaping or replacing sensitive characters (`{`, `}`, `\`). Full-width equivalents (`｛`, `｝`, `＼`) offer a safe method to preserve readability while neutering tag functionality.