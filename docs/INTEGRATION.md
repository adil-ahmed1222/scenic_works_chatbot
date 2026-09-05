# Integration Guide

Embed the Scenic Works assistant on the existing website **without rebuilding it**.

## Production snippet

Place this before `</body>` on https://adroitiame.com (all templates, including PHP layouts):

```html
<script src="https://chat.adroitiame.com/widget.js" async></script>
```

The script:

1. Injects a transparent iframe pointing at `/embed`.
2. Mounts automatically.
3. Expands from a floating launcher into the chat window.
4. Stays anchored to the same corner in English and Arabic; only the text direction changes.

## Local / staging

```html
<script src="http://localhost:3000/widget.js"></script>
```

## CORS checklist

The iframe origin is `chat.adroitiame.com`, not the parent page. Railway `ALLOWED_ORIGINS` must include that widget origin.

## Behaviour

| Feature | Detail |
| --- | --- |
| Language | Detected from the user message (and browser language for UI chrome) |
| Memory | Signed `session_id` + `session_token` in `localStorage`; last 10 turns sent to the LLM |
| Voice | 🔊 Listen on assistant messages |
| Leads | Form appears on quotation / proposal / stand / event / pricing intent |
| Mobile | Full-viewport height, `min(400px, 100vw - 2rem)` width |
| Theme | Scenic Works dark gold (dark mode default) |

## Content security

If the parent site sets a strict `Content-Security-Policy`, allow:

```
script-src https://chat.adroitiame.com
frame-src https://chat.adroitiame.com
```

## Uninstall

Remove the script tag. No other site files are modified.
