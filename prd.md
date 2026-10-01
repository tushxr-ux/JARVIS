# JARVIS — Product Requirements Document

**Version**: MARK LIII  
**Last Updated**: 2026-09-25  
**Status**: Active Development

---

## 1. Product Vision

JARVIS is a local-first AI assistant desktop application inspired by Tony Stark's fictional AI. It is built on Google's Gemini Live multimodal API and runs as a native Python/PyQt6 desktop application on Windows, macOS, and Linux. The product goal is to provide a premium, responsive, and intelligent voice-driven assistant that feels **present** and **alive** — not like a chatbot or widget, but like an actual AI companion with authority to act on behalf of the user.

---

## 2. User Goals

- **Voice-first interaction**: Talk to JARVIS naturally; it responds via audio
- **System control**: Control the OS, apps, files, browser, and settings via voice
- **Proactive assistance**: JARVIS surfaces relevant information unprompted
- **Long-term memory**: JARVIS remembers facts about the user across sessions
- **Code and file actions**: JARVIS can read, write, and modify project files when authorized
- **Remote control**: Control JARVIS from a phone via a web dashboard

---

## 3. Core Features

### 3.1 Voice Pipeline
- Real-time STT via Gemini Live API (streaming PCM audio, 16kHz int16)
- Real-time TTS via Gemini Live audio output (24kHz int16)
- Audio-reactive HUD that responds to both mic input and speaker output amplitude
- Microphone mute/unmute (F4 key or UI button)
- Voice interrupt mid-speech (Escape key or UI button)

### 3.2 Wake Word System (Optional)
- Local "Hey Jarvis" detection via openwakeword (ONNX, CPU-only)
- When enabled: JARVIS starts SLEEPING; wake word triggers LISTENING
- When disabled: JARVIS starts LISTENING immediately
- Auto-sleep timeout: configurable (default 120 seconds of silence, wake-word mode only)
- Manual WAKE / SLEEP controls always available

### 3.3 AI / LLM Integration
- Model: gemini-3.1-flash-live-preview via Google Gemini Live API
- Session resumption: conversation context preserved across reconnects
- Context window compression for unlimited session length
- Proactive mode: AI can initiate unprompted check-ins
- Morning briefing: news summary + personalized greeting on startup

### 3.4 Long-Term Memory
- User facts stored in memory/long_term.json
- Categories: identity, preferences, projects, relationships, wishes, notes
- End-of-session summary saved for context continuity
- Memory panel in UI for inspection and deletion

### 3.5 Action System (Tools)
- **Inline tools**: system_status, screen_process, close_camera, manage_monitor, shutdown_jarvis, save_memory, recall_memory, undo
- **Discovered actions** (actions/): browser, OS, file, web search, system monitor, code, etc.
- **Plugins** (plugins/): user-extensible, auto-discovered at startup
- Tool registry prevents name conflicts

### 3.6 Confirmation Gate
- Irreversible actions trigger a UI confirmation banner
- User must click CONFIRM on-screen (model cannot self-confirm)
- Applies to: shutdown, restart, WiFi toggle, destructive file operations

### 3.7 Remote Dashboard
- FastAPI web server running locally on a random port
- Phone connects via QR code or 6-digit key
- Phone can send voice/text commands and view conversation log
- Encrypted communication with session-scoped keys

### 3.8 Visual HUD
- Central animated quantum ferrofluid sphere (custom PyQt6/numpy canvas)
- Audio-reactive: responds to microphone (listening) and speaker output (speaking)
- State-driven visual behavior per JARVIS state
- System metrics (CPU, RAM, GPU, temperature, network)
- Deep space starfield background

---

## 4. JARVIS Interaction Model

```
User speaks -> Mic captures PCM -> Gemini Live processes
-> AI: tool call or text response
-> If tool: execute -> return result -> AI narrates
-> Audio response plays -> HUD reacts to audio
```

---

## 5. Voice Lifecycle State Machine

```
Type JarvisState = 
  | "sleeping"    -- mic gated, minimal animation
  | "waking"      -- transition animation, not yet listening
  | "listening"   -- mic active, audio-reactive HUD
  | "thinking"    -- tool detected, controlled turbulence
  | "processing"  -- action executing
  | "speaking"    -- TTS playing, audio-reactive HUD
  | "success"     -- brief positive pulse
  | "error"       -- warning visual, error message
```

---

## 6. Agent Capabilities

| Domain | Examples |
|--------|---------|
| File system | Read, write, move, rename, delete files |
| Browser | Open URLs, click elements, fill forms |
| OS settings | Volume, brightness, WiFi, Bluetooth |
| Application control | Open/close apps, window management |
| Code | Read, write, refactor, analyze code files |
| Web search | DuckDuckGo, news, research, pricing |
| System monitor | CPU/RAM/GPU/temperature alerts |
| Reminders | Timed notifications |
| Screen capture | Screenshot analysis, live camera feed |
| Memory | Store and recall user facts |

---

## 7. Permission Model

| Action Type | Behavior |
|------------|---------|
| Read files/code | Auto-allowed |
| Write normal files | Auto-allowed |
| Web searches | Auto-allowed |
| System settings (reversible) | Auto-allowed + undo stack |
| Destructive file ops | Requires confirmation banner |
| System shutdown/restart | Requires confirmation banner |
| Network/security changes | Requires confirmation banner |
| Secrets/API keys | Never exposed to model |

---

## 8. Non-Functional Requirements

- Startup time: < 5 seconds to LISTENING state
- Response latency: < 1 second from speech end to AI audio start
- HUD animation: 30-60 fps, adapts based on activity
- Cross-platform: Windows primary, macOS and Linux supported
- Wake word: fully local, no internet required
- No raw secrets exposed in UI or model context

---

## 9. Success Criteria

- [ ] Voice conversation flows naturally without dropped turns
- [ ] HUD orb visually reacts to actual microphone and speaker audio
- [ ] Wake word reliably triggers within 1 second
- [ ] Auto-sleep only triggers in wake-word mode, not by default
- [ ] All buttons have correct labels, hover states, consistent styling
- [ ] Sensitive actions require confirmation gate
- [ ] Session context preserved across reconnects
- [ ] Settings UI controls all have real effects
