# JARVIS — Coding Rules

**Version**: MARK LIII  
**Last Updated**: 2026-09-25

---

## 1. General Principles

1. **Audit before modifying**: Read and understand existing code before changing it.
2. **Preserve working functionality**: Do not remove or bypass working features without reason.
3. **No fake integrations**: Do not claim a feature is installed unless it actually works.
4. **No silent failures**: Every action must have proper error handling.
5. **No secrets in model context**: Never inject API keys, passwords, or tokens into prompts.

---

## 2. Python Conventions

### 2.1 Style
- Python 3.11+ features are allowed (match/case, TaskGroup, ExceptionGroup)
- Type hints on all public functions
- `from __future__ import annotations` at top of modules that use forward references
- 4-space indentation, no tabs
- Max line length: 110 characters (following existing codebase)

### 2.2 Naming
| Pattern | Convention |
|---------|-----------|
| Classes | `PascalCase` |
| Public functions/methods | `snake_case` |
| Private functions/methods | `_snake_case` |
| Constants | `UPPER_SNAKE_CASE` |
| Private constants | `_UPPER_SNAKE_CASE` |
| Qt signals | `snake_case` (PyQt convention) |

### 2.3 Async Rules
- All Gemini Live communication runs in the single asyncio event loop
- Never call blocking code directly in async functions — use `run_in_executor` or `asyncio.to_thread`
- Qt UI updates from async code must use Qt signals (never call Qt methods directly from async)
- Use `asyncio.TaskGroup` for concurrent session tasks
- Use `asyncio.Queue(maxsize=N)` for audio buffers to prevent unbounded growth

### 2.4 Threading Rules
- `main.py`'s asyncio loop runs in a daemon thread (`threading.Thread`)
- All Qt widget manipulation must happen on the Qt main thread
- Use `loop.call_soon_threadsafe()` to post work from threads to the asyncio loop
- Use Qt signals (`pyqtSignal`) to post work from threads/asyncio to the Qt thread
- Never call `widget.update()` or `widget.setText()` from non-Qt threads

---

## 3. State Management

### 3.1 JARVIS State Source of Truth
- `_awake` (bool in JarvisLive): actual mic gate state
- `_is_speaking` (bool in JarvisLive): actual TTS playing state
- `hud.state` (str in HudCanvas): visual state for animation
- `hud.speaking` (bool): mirrors `_is_speaking` via `set_speaking()`
- `hud.muted` (bool): mirrors UI mute button state

**Rule**: Visual state MUST reflect actual system state. Never set `hud.state = "LISTENING"` when mic is closed.

### 3.2 State Transitions

Always use `set_state()` on the UI wrapper (thread-safe via signal) — never set `hud.state` directly from non-Qt threads.

```python
# Correct (from any thread):
self.ui.set_state("LISTENING")  # -> _state_sig.emit() -> _apply_state()

# Wrong (from async/non-Qt thread):
self.ui.hud.state = "LISTENING"  # not thread-safe
```

---

## 4. Tool / Action Conventions

### 4.1 New Actions
Every file in `actions/` that wants to be a tool must define a `TOOL` dict:

```python
TOOL = {
    "name": "tool_name",
    "description": "What this tool does. Written for the AI model.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "param": {"type": "STRING", "description": "..."}
        },
        "required": ["param"]
    },
    "run": run_function,  # callable(args: dict, ctx: dict) -> str
}
```

- `run()` is called in an executor thread — it may block
- Return value is a string passed back to the model
- Raise exceptions for genuine failures (caller will wrap in error response)
- Log actions to undo stack via `core.undo` for reversible changes

### 4.2 Sensitive Actions

Actions that require confirmation must call `core.confirm.request()` and block until answered. The confirmation gate is wired at session startup.

```python
from core import confirm as confirm_gate

ok = confirm_gate.request("Delete 47 files?", "This cannot be undone.")
if not ok:
    return "Cancelled by user."
```

---

## 5. UI Conventions

### 5.1 Widget Creation
- Use `QFont("Courier New", size, weight)` — the app's monospace UI font
- Always set `setCursor(Qt.CursorShape.PointingHandCursor)` on clickable widgets
- All stylesheets use f-strings with `C.*` color constants (never hardcode hex in widgets)
- Always provide hover state in stylesheets for interactive elements

### 5.2 Overlay Panels
- Must extend `_HudOverlay` (not `QWidget`) to fix ghost-rendering on hide
- Fixed width, auto-height via `adjustSize()`
- Positioned by `_centre_overlay()` helper in MainWindow
- Always have a CLOSE / CANCEL button as default (not the destructive action)

### 5.3 New Settings
- Add field to `config/api_keys.json` schema
- Add getter/setter pair to `memory/config_manager.py`
- Connect UI control to config via signal/slot in MainWindow
- Test that the setting actually has a functional effect

---

## 6. Audio Rules

1. Mic callback (`callback` in `_listen_audio`) must be non-blocking — only queue push
2. `_pcm_level()` is called in the callback — must never raise
3. Audio level fed to HUD is cosmetic — failures here must never affect audio streaming
4. `set_audio_level()` on HudCanvas is thread-safe (single float write with GIL)
5. Wake-word detector (`WakeWordDetector.feed()`) runs in mic callback — must be O(1)
6. Audio streams are opened inside the session TaskGroup and closed on TaskGroup exit

---

## 7. Security Rules

1. **Never** include `api_keys.json` contents in model prompts
2. **Never** grant unrestricted filesystem access — use project-scoped paths
3. **Always** go through `confirm_gate` for destructive or irreversible actions
4. Natural-language commands never bypass permission checks
5. Remote dashboard keys are session-scoped and expire after 10 minutes
6. Do not expose `.env` or credential files to the model context

---

## 8. Error Handling

```python
# Pattern for tool execution
try:
    result = do_thing()
except SpecificError as e:
    self.speak_error(tool_name, e)  # logs + speaks error
    return f"Tool failed: {e}"
except Exception as e:
    traceback.print_exc()
    self.speak_error(tool_name, e)
    return f"Unexpected error in {tool_name}: {e}"
```

- Never silently swallow exceptions in production paths
- User-facing errors: short, plain-language, actionable
- Dev-facing errors: full traceback to stdout
- Audio errors: `speak_error()` so JARVIS acknowledges the failure verbally

---

## 9. Performance Rules

1. HudCanvas `paintEvent` must complete in < 16 ms (60 fps target during active states)
2. Use pre-cached QPen arrays — never allocate QPen inside paintEvent
3. Use numpy vectorized operations for sphere point calculations
4. Adapt timer interval: 16ms when active, 33ms when idle
5. Skip repaint if nothing changed (HudCanvas `_paint_tick` throttle)
6. Audio context cleanup: always close sounddevice streams in finally blocks
7. Memory leaks: always cancel/stop timers and close streams on widget destruction
8. Reduce animation when window not visible (Qt `isVisible()` check where appropriate)

---

## 10. Testing

- Run `python -m py_compile main.py ui.py` to check for syntax errors before committing
- Run the app and verify: mic captures, TTS plays, HUD animates, wake/sleep cycle works
- Test wake-word toggle: enable -> goes SLEEPING -> say "Hey Jarvis" -> wakes
- Test confirmation gate: issue a destructive command -> banner appears -> cancel -> not executed
- Test session resumption: trigger a reconnect (change voice) -> conversation context preserved
- Test tool execution: "what's my CPU usage?" -> system_status tool called -> result spoken
