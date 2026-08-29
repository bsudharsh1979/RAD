# Security

Threats addressed:

- Prompt injection: documents wrapped as DATA.
- Malicious notebook code: never executed; flagged.
- Secrets: `.env` not committed.
- Uploads: size + suffix allowlist; no path traversal.
- SSRF: `is_safe_url` helper for future fetches.
- XSS: React text escaping; no `dangerouslySetInnerHTML` on course markdown.
- API abuse: naive per-IP rate limit on tutor.
- Provider keys only on the API, never in the browser bundle.

Do not give agents a Python REPL in production — the course itself calls that a bad idea.
