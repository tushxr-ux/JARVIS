# JARVIS — Memory & Project Context

**Version**: MARK LIII  
**Last Updated**: 2026-09-25

---

## 1. Critical Project Facts

- **Project type**: Python/PyQt6 desktop application (NOT a web/React/Next.js app)
- **This is NOT a fresh build** — it is an existing, fully functional system
- **Entry point**: `main.py` (run with `python main.py`)
- **UI framework**: PyQt6 with custom QPainter canvas (`HudCanvas` in `ui.py`)
- **AI backend**: Google Gemini Live API via `google-genai` SDK
- **Primary TTS/STT**: Gemini Live audio streaming (NOT EdgeTTS/Kokoro for primary voice)
- **Audio**: sounddevice (libsoundio) for mic input and speaker output
- **No React Bits Pro**: The project does NOT use React, Next.js, or React Bits Pro. Those instructions in the prompt were aspirational; the actual codebase is PyQt6.

---

## 2. What Actually Works (Verified by Audit)

### Working Features
- Gemini Live session with real-time audio streaming
- Audio-reactive HudCanvas orb (responds to actual mic + TTS amplitude)
- Wake word detection via openwakeword ("Hey Jarvis") — optional
- Wake/sleep state machine (`_awake`, `_run_sleep_watch`)
- Session resumption (conversation context preserved across reconnects)
- Memory system (long_term.json, save_memory, recall_memory tools)
- Confirmation gate for destructive actions
- Remote dashboard (FastAPI, QR code, phone pairing)
- Action system: 20+ tools auto-discovered from actions/
- Plugin system: extensible via plugins/ directory
- Undo stack for reversible actions
- Live camera feed
- Screen capture and visual analysis
- UI color theming (hue-shift algorithm on C.* palette)
- File drag-and-drop for context attachment
- Audio device picker (mic + speakers)
- Settings overlays (customize, audio, memory, plugins, wake word)
- Morning briefing (news + greeting on startup)
- Proactive mode (AI-initiated check-ins)
- Background topic monitoring
- System metrics overlay (CPU/RAM/GPU/temp/network)
- Keyboard shortcuts: F4 (mute), F11 (fullscreen), Escape (interrupt)

### Known Issues (from audit)

1. **Auto-sleep timing issue**: `WAKE_SLEEP_TIMEOUT = 120.0` (2 minutes) can feel aggressive for users who pause between voice commands. The sleep watch only runs in wake-word mode, but users who enable wake word may not realize the 2-minute timer starts.

2. **`_asst_name` has a typo**: Line 355 in main.py: `self._asst_name = "JARVI    S"` — has extra spaces. It is overwritten from config on each session build, so it only affects the very first log line before config loads.

3. **Prompt.txt grammar issue**: Line 35: "only for complex, multi-step planning (3+ steps) and call it if user it really spesifize it" — "spesifize" should be "specifies", and the grammar is awkward.

4. **Prompt.txt line 40 grammar**: "wants to open a video = youtube. Always know the context for better User Experience" — fragmented sentence, mixed capitalization.

5. **main.py line 1742**: `ui.root.mainloop()` — `mainloop()` is a Tkinter method; the actual event loop is driven by PyQt6's `app.exec()` inside `JarvisUI`. This line appears to be dead code or from a Tkinter era — needs verification.

6. **ui.py line 355 comment**: Uses corrupted encoding characters (â€" instead of em dash, etc.) — encoding artifact in the file, doesn't affect runtime but affects readability.

7. **Tooltip gaps**: Several buttons lack tooltips. Settings, Wake Word, and Protocol buttons are not fully documented for first-time users.

8. **Settings panel**: The `CustomizeOverlay` does not expose Auto-sleep timeout or a per-user configurable sleep timeout setting. Users must accept the hardcoded 120-second timeout.

---

## 3. Architectural Decisions to Preserve

### DO NOT CHANGE:
1. The asyncio + threading architecture (`asyncio.run()` in daemon thread, Qt on main thread)
2. The Qt signal pattern for cross-thread UI updates (`_log_sig`, `_state_sig`, etc.)
3. The action discovery system (`core/action_loader.py`, `TOOL` dict convention)
4. The plugin system (`core/plugin_loader.py`)
5. Session resumption (`self._resume_handle` in-memory, carried across reconnect)
6. The confirmation gate architecture (core/confirm.py binding)
7. The `_pcm_level()` approach for audio amplitude

### CAN BE IMPROVED:
1. Auto-sleep timeout should be configurable in settings (not just hardcoded)
2. The HudCanvas can have more state-specific visual variations
3. Settings overlay can be expanded with more user-controllable options
4. Button labels and copy can be cleaned up for consistency
5. The `_asst_name` initialization typo can be fixed
6. Prompt.txt grammar issues can be corrected

---

## 4. Important Dependencies

| Package | Version | Why |
|---------|---------|-----|
| google-genai | >=2.8.0 | Gemini Live API |
| PyQt6 | latest | UI framework |
| sounddevice | latest | Audio I/O |
| numpy | latest | PCM analysis, sphere math |
| fastapi + uvicorn | latest | Remote dashboard |
| openwakeword | optional | Wake word detection |
| opencv-python | latest | Camera capture |
| Pillow | latest | Image processing |
| psutil | latest | System metrics |

---

## 5. Configuration File Schema (api_keys.json)

```json
{
  "gemini_api_key": "AIza...",
  "assistant_name": "JARVIS",
  "user_name": "",
  "voice_name": "Charon",
  "ui_color": "#00e5ff",
  "wake_word_enabled": false,
  "morning_brief_enabled": true,
  "input_device": "",
  "output_device": "",
  "os_system": "windows",
  "camera_index": 0
}
```

---

## 6. Sleep/Wake Behavior Details

### Current behavior:
- `wake_word_enabled=False` (default): JARVIS is ALWAYS awake after connect. Auto-sleep NEVER runs.
- `wake_word_enabled=True`: JARVIS starts SLEEPING. Auto-sleep fires after 120s of no user speech.

### The "auto-sleep problem" in the prompt:
The prompt says "JARVIS works initially, but after a few minutes of no speaking it goes to sleep." This only happens when wake word is enabled. With wake word disabled (the default), JARVIS does NOT auto-sleep. The fix needed is:
1. Make auto-sleep timeout configurable in settings (never / 5m / 10m / 30m / 1h)
2. Default to a longer timeout or "never" for better UX
3. Make the behavior clear in the settings UI

---

## 7. React Bits Pro / Eclipse — Reality Check

The original prompt requested React Bits Pro Eclipse and AI Blob components. However:
- This is a PyQt6 application, not a React/web app
- The existing HudCanvas is a fully custom PyQt6 canvas that already provides the orb concept
- Integrating React components would require rewriting the entire UI as a web app
- The correct path is to **enhance the existing HudCanvas** to achieve the Eclipse aesthetic

**Recommendation**: Enhance HudCanvas to support more state-driven visual behavior and add Eclipse-like corona/glow effects using QPainter gradients, rather than attempting to embed a React component in a Python app.

---

## 8. Session Context for Next Developer

If continuing work on this project:

1. The project runs as `python main.py` from the project root
2. First run shows `SetupOverlay` to enter Gemini API key
3. The HUD orb is the `HudCanvas` class in `ui.py` (~line 390)
4. The voice session engine is `JarvisLive` in `main.py` (~line 352)
5. Wake/sleep state lives in `JarvisLive._awake` and `JarvisLive._wake_enabled`
6. To add a new tool: create `actions/mytool.py` with a `TOOL` dict
7. To change the system prompt: edit `core/prompt.txt`
8. To change voice list: edit `AVAILABLE_VOICES` in `memory/config_manager.py`
9. Audio amplitude flows: mic/speaker -> `_pcm_level()` -> `HudCanvas.set_audio_level()`
10. UI state flows: `JarvisLive.set_state()` -> `ui.set_state()` -> `_state_sig.emit()` -> `_apply_state()` -> `hud.state = ...`
