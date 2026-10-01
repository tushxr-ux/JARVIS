# JARVIS — Architecture Document

**Version**: MARK LIII  
**Last Updated**: 2026-09-25

---

## 1. Technology Stack

| Layer | Technology |
|-------|-----------|
| UI Framework | PyQt6 (native widgets + custom QPainter canvas) |
| AI Model | Google Gemini Live API (gemini-3.1-flash-live-preview) |
| Audio I/O | sounddevice (libsoundio backend) |
| Audio Analysis | numpy (PCM RMS computation) |
| Vision | OpenCV + Pillow (camera capture, screen capture) |
| Web Server | FastAPI + uvicorn (remote dashboard) |
| Memory | JSON flat files (long_term.json, api_keys.json) |
| Wake Word | openwakeword (ONNX, CPU-only) — optional |
| Async Runtime | asyncio (Python 3.11+, TaskGroup) |
| Threading | threading.Thread for UI-async bridge |

---

## 2. Directory Structure

```
JARVIS/
├── main.py              # Entry point, JarvisLive class (async session engine)
├── ui.py                # JarvisUI / MainWindow, HudCanvas, all Qt widgets
├── requirements.txt     # Python dependencies
├── setup.py             # Installer/autostart helper
├── core/
│   ├── action_loader.py # Auto-discovers actions/*.py TOOL dicts
│   ├── audio_devices.py # Enumerate/resolve audio devices
│   ├── confirm.py       # Confirmation gate (binds UI show/hide to core)
│   ├── installer.py     # Self-installer helper
│   ├── llm_client.py    # LLM utilities (non-Live requests)
│   ├── plugin_loader.py # Auto-discovers plugins/
│   ├── prompt.txt       # System prompt for JARVIS
│   ├── stt.py           # STT utilities (non-Live use)
│   ├── tts.py           # EdgeTTS / Kokoro / ElevenLabs engines
│   ├── undo.py          # Undo stack for reversible actions
│   └── wake_word.py     # WakeWordDetector (openwakeword)
├── actions/             # Auto-discovered tool handlers
│   ├── browser_control.py
│   ├── code_helper.py
│   ├── computer_control.py
│   ├── computer_settings.py
│   ├── desktop.py
│   ├── dev_agent.py
│   ├── file_controller.py
│   ├── file_processor.py
│   ├── open_app.py
│   ├── reminder.py
│   ├── screen_processor.py
│   ├── system_monitor.py
│   ├── web_search.py
│   └── youtube_video.py
├── config/
│   ├── api_keys.json    # All persistent configuration (API key, settings)
│   └── __init__.py      # OS detection helpers
├── dashboard/
│   ├── server.py        # FastAPI dashboard server
│   └── static/
│       ├── app.html     # Remote dashboard web UI
│       └── login.html   # Auth page
├── memory/
│   ├── config_manager.py # Read/write api_keys.json settings
│   ├── memory_manager.py # Long-term memory CRUD
│   └── long_term.json    # User facts storage
└── plugins/             # User-extensible plugin directory
    └── _template.py
```

---

## 3. Frontend Architecture (PyQt6)

### 3.1 Main Window Hierarchy

```
MainWindow (QMainWindow)
├── Header bar (_build_header)
│   ├── Logo + protocol badge
│   ├── Status pill (ONLINE/OFFLINE/SLEEPING)
│   ├── System metrics (CPU/RAM/NET pills)
│   └── Action buttons (Mute, Remote, Interrupt, Settings, etc.)
├── Body (QHBoxLayout)
│   ├── Left panel (_build_left_panel) -- metrics, file drop zone
│   ├── Center column (QSplitter vertical)
│   │   ├── HUD area (QStackedWidget)
│   │   │   ├── HudCanvas (custom QPainter, animated orb)
│   │   │   └── Camera feed widget
│   │   └── Content panel (LogWidget + text display)
│   └── Right panel (_build_right_panel) -- quick actions, status
├── Footer bar (_build_footer)
│   ├── Text input (QLineEdit)
│   └── Control buttons
└── Floating overlays (children of central widget, no layout)
    ├── SetupOverlay     -- API key entry
    ├── CustomizeOverlay -- Name, voice, color settings
    ├── ConfirmBanner    -- Irreversible action gate
    ├── MemoryOverlay    -- Memory inspection/deletion
    ├── AudioDeviceOverlay -- Mic/speaker picker
    ├── PluginManagerOverlay -- Plugin ON/OFF
    ├── RemoteKeyOverlay -- QR code / key for phone
    └── _CameraPreview   -- Thumbnail of last capture
```

### 3.2 HudCanvas (ui.py: HudCanvas)

Custom QPainter widget. Animation driven by QTimer at 16-33 ms intervals.

**Layers (rendered in order)**:
1. Deep space starfield (80 twinkling stars, numpy-vectorized)
2. Molten core radial aura (QRadialGradient glow)
3. 3D Quantum Ferrofluid Core (950-point Fibonacci sphere, rotated per frame)
4. Face image overlay (if face.png present)
5. Corner HUD telemetry readouts (CPU/RAM/NET/GPU/TMP)
6. Status text with bloom glow (LISTENING / SPEAKING / THINKING / etc.)

**Audio reactivity**:
- `set_audio_level(level: float)`: thread-safe entry point
- `_live_amp`: raw amplitude, decays at 0.86 per frame
- `_amp_disp`: smoothed display amplitude (lerp at 0.45)
- Affects: sphere scale, halo radius, rotation speed, surface lobes

---

## 4. Backend Architecture (main.py)

### 4.1 JarvisLive Class

The core async session engine. Runs in a dedicated daemon thread (`threading.Thread`), driving `asyncio.run(jarvis.run())`.

**Key state**:
- `_awake: bool` — whether mic is active (gated by wake-word)
- `_is_speaking: bool` — whether TTS audio is currently playing
- `_wake_enabled: bool` — whether wake-word mode is on
- `session` — active Gemini Live session object
- `_resume_handle` — session resumption token (in-memory only)
- `_last_user_speech` — monotonic timestamp for auto-sleep timer

**Concurrent async tasks (TaskGroup)**:
```
_watch_reconnect()    -- handles voluntary session rebuilds
_send_realtime()      -- drains out_queue -> Gemini Live audio input
_listen_audio()       -- mic callback -> out_queue
_receive_audio()      -- Gemini response -> parse transcripts, tools, audio
_play_audio()         -- audio_in_queue -> sounddevice output
_run_system_monitor() -- CPU/RAM/GPU alerts every 10s
_run_background_monitor() -- topic monitoring every 30 min
_run_proactive_mode() -- AI check-ins every 60s when idle
_run_sleep_watch()    -- auto-sleep timer (wake-word mode only)
_relay_phone_audio()  -- phone mic -> Gemini (dashboard only)
```

### 4.2 Audio Pipeline

```
Microphone (sounddevice InputStream, 16kHz int16)
    |
    +--> Wake word gate (if enabled + sleeping):
    |       WakeWordDetector.feed() -> on_detect() -> wake()
    |
    +--> PCM bytes -> out_queue (asyncio.Queue, maxsize=200)
    |
    +--> _pcm_level() -> HudCanvas.set_audio_level()  [cosmetic]

out_queue -> _send_realtime() -> session.send_realtime_input(audio=Blob)

session.receive() -> response.data (audio bytes)
    |
    +--> audio_in_queue (asyncio.Queue, 2400-byte slices)
    |
    +--> _play_audio() -> sounddevice RawOutputStream (24kHz int16)
    |
    +--> _pcm_level() -> HudCanvas.set_audio_level()  [cosmetic]
```

### 4.3 Tool Execution Pipeline

```
session.receive() -> response.tool_call.function_calls
    |
    v
_execute_tool(fc) -- dispatches by name:
    ├── Inline tools (save_memory, recall_memory, undo, screen_process, etc.)
    ├── Action registry (actions/*.py TOOL dicts, run via executor thread)
    └── Plugin registry (plugins/*.py, run via executor thread)
    |
    v
session.send_tool_response(function_responses=[...])
```

### 4.4 Wake/Sleep State Machine

```
Startup:
  wake_word_enabled=True  -> _awake=False, state=SLEEPING
  wake_word_enabled=False -> _awake=True,  state=LISTENING

Wake triggers:
  - "Hey Jarvis" detected by WakeWordDetector
  - _ui_wake_manual() -- user clicks WAKE button
  - Remote dashboard command (auto-wakes if asleep)

Sleep triggers:
  - _run_sleep_watch(): silence > WAKE_SLEEP_TIMEOUT (120s) -- wake-word mode ONLY
  - _ui_wake_manual() -- user clicks SLEEP button
  - _ui_wake_toggle(enable=True) -- enabling wake word puts JARVIS to sleep

Auto-sleep only fires when:
  self._wake_enabled AND self._awake AND NOT speaking AND
  (monotonic() - _last_user_speech) > _wake_sleep_timeout
```

---

## 5. Configuration

All persistent settings stored in `config/api_keys.json`:

```json
{
  "gemini_api_key": "...",
  "assistant_name": "JARVIS",
  "user_name": "",
  "voice_name": "Charon",
  "ui_color": "#00e5ff",
  "wake_word_enabled": false,
  "morning_brief_enabled": true,
  "input_device": "",
  "output_device": "",
  "os_system": "windows"
}
```

---

## 6. Security Architecture

| Concern | Mitigation |
|---------|-----------|
| API key exposure | Stored in local JSON, never sent to AI context |
| Confirmation gate bypass | UI confirms, not model — confirmation is physical click |
| Remote dashboard auth | Session-scoped 6-digit key, 10-min expiry, encrypted |
| Destructive commands | core/confirm.py gate — blocks until UI answer |
| Undo safety | core/undo.py tracks all reversible changes |

---

## 7. Known Architectural Constraints

1. **Single asyncio loop**: all Gemini Live communication runs in one event loop; blocking calls use `run_in_executor`
2. **PyQt6 thread safety**: all UI updates must go through Qt signals (`_log_sig`, `_state_sig`, etc.)
3. **Session resumption**: in-memory only; fresh process always starts new session context
4. **Wake word model**: openwakeword requires ~130 MB download on first enable; not bundled
5. **TTS architecture**: primary TTS is Gemini Live audio output; the `core/tts.py` engines (EdgeTTS, Kokoro, ElevenLabs) are available for plugin use but are NOT the main voice
6. **Face image**: `face.png` at project root is optional; HudCanvas renders without it
