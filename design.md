# JARVIS — Design Document

**Version**: MARK LIII  
**Last Updated**: 2026-09-25

---

## 1. Visual Identity

JARVIS is an AI that feels **present**. The interface should communicate intelligence, awareness, and authority without visual clutter. It is not a dashboard, not a chatbot bubble, and not a generic SaaS app.

**Design principles**:
- **Alive**: The central orb is never static. Even at rest it breathes.
- **Intentional**: Every visual element has a purpose.
- **Minimal**: The orb dominates. Controls are subordinate.
- **Cinematic**: Premium, high-contrast, dark aesthetic.

---

## 2. Color System

### Primary Palette (Quantum Core — Electric Cyan)

| Token | Hex | Usage |
|-------|-----|-------|
| `BG` | `#000408` | Deepest void background |
| `PANEL` | `#010812` | Panel backgrounds |
| `PANEL2` | `#010e1a` | Elevated surfaces |
| `BORDER` | `#0a2540` | Default borders |
| `BORDER_B` | `#1a5080` | Bright/active borders |
| `PRI` | `#00e5ff` | Electric plasma cyan (primary accent) |
| `PRI_DIM` | `#0088aa` | Dimmed cyan |
| `PRI_GHO` | `#001d2e` | Hover ghost cyan |
| `TEXT` | `#a8f0ff` | Primary text |
| `TEXT_DIM` | `#3a8aaa` | Dimmed text |
| `TEXT_MED` | `#5ab0cc` | Medium text |

### Status Colors (Fixed — Not Hue-Linked)

| Token | Hex | Usage |
|-------|-----|-------|
| `ACC` | `#ff6600` | Neon orange (Iron Man accent) |
| `ACC2` | `#ffb700` | Gold/amber (orb core, particle sphere) |
| `GREEN` | `#00ff99` | Success/OK state |
| `RED` | `#ff1144` | Error/critical state |

### Hue Theming
The full palette is hue-derivable from the primary accent. When the user changes the UI color, all `_HUE_LINKED` tokens are recalculated via HSV shift while preserving brightness/saturation ratios. Status colors stay fixed.

---

## 3. Typography

| Usage | Font | Size | Weight |
|-------|------|------|--------|
| HUD status text | Courier New | 11 | Bold |
| Corner metrics | Courier New | 8 | Bold |
| Log widget | Courier New | 9 | Normal |
| Overlays/headings | Courier New | 9-13 | Bold |
| Button text | Courier New | 7-10 | Bold |
| Header logo | Orbitron (web) | 17 | Black (900) |
| Header pills | Share Tech Mono | 10 | Bold |
| Body text | Rajdhani | 9 | Medium |

The desktop app uses Courier New as the primary code-style font. The web dashboard uses Orbitron/Rajdhani/Share Tech Mono from Google Fonts.

---

## 4. The HUD Orb (HudCanvas)

### 4.1 States and Visual Behavior

| State | Color Scheme | Animation |
|-------|-------------|-----------|
| SLEEPING | Muted red-magenta | Near-static, minimal breathing |
| LISTENING | Gold/amber particles | Slow organic rotation, mic-reactive |
| THINKING | Gold + heat vortices | Increased attractor activity |
| PROCESSING | Gold + heat vortices | Controlled spectral turbulence |
| SPEAKING | Gold + heat vortices | TTS audio amplitude drives scale/halo |
| MUTED | Red-magenta override | Minimal movement |
| ERROR | — (text overlay) | Controlled warning |

### 4.2 Audio Reactivity

```
Audio input (mic or TTS) -> _pcm_level() -> [0.0, 1.0]
  -> HudCanvas.set_audio_level(level)
     -> _live_amp = max(current, level)   [peak-hold]

Per frame (_step() @ 33ms):
  _live_amp *= 0.86                       [fast decay]
  _amp_disp += (_live_amp - _amp_disp) * 0.45  [smooth]
  amp = _amp_disp

amp drives:
  _tgt_scale = base_scale + amp * 0.13 (speaking) or * 0.06 (listening)
  _tgt_halo  = base_halo  + amp * 95.0 (speaking) or * 75.0 (listening)
  sphere rotation speed *= (1.0 + amp * 1.6)
  surface lobe += amp * 0.18 * sin(...)
  attractor heat += (2.4 + amp * 2.0) * att
```

### 4.3 Sphere Geometry

- 950-point Fibonacci sphere lattice (precomputed at init)
- 5 dynamic attractor dimple vortices (slowly orbiting)
- Harmonic surface lobes (3 overlapping sinusoids)
- Perspective projection with FOV = fw * 1.6
- 8 depth/heat tier QPen cache (no per-frame allocation)
- Back-to-front rendering (painter's algorithm)
- Outer ferrofluid rim spikes (~80 spires)

---

## 5. Layout

### 5.1 Main Window Structure

```
┌─────────────────────────────────────────────────────────┐
│ HEADER: Logo | Status | Metrics | Controls              │
├──────────┬──────────────────────────────┬───────────────┤
│  LEFT    │      CENTER (HUD)            │  RIGHT        │
│  panel   │                              │  panel        │
│ (148px)  │   [HudCanvas / Camera]       │ (340px)       │
│          │         ↕ splitter           │               │
│  Metric  │   [Content / Log panel]      │  Quick        │
│  bars    │                              │  actions      │
│  File    │                              │  Log          │
│  drop    │                              │               │
├──────────┴──────────────────────────────┴───────────────┤
│ FOOTER: Text input | Controls                           │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Responsive Behavior

- Minimum window: 820 × 580 px
- Default window: 980 × 700 px
- Left panel: fixed 148px wide
- Right panel: fixed 340px wide
- Center: flexible, expands with window
- HUD:Content splitter: 3:1 default ratio

---

## 6. Buttons

### Button States

Every interactive button must have:
- **Default**: transparent bg, colored text, 1px solid border
- **Hover**: ghost background fill (PRI_GHO or equivalent)
- **Active/Pressed**: slightly brighter border
- **Disabled**: TEXT_DIM text, BORDER border
- **Loading**: text changes (e.g., "APPLYING…")
- **Focus**: visible focus ring (keyboard navigation)

### Button Label Standards

| Wrong | Correct |
|-------|---------|
| "Activate" | "WAKE JARVIS" |
| "OK" | "CONFIRM" or "APPLY" |
| "Cancel" | "CANCEL" (consistent case) |
| "Click here" | Specific action |

All buttons use ALL_CAPS for primary actions, Title Case for secondary.

---

## 7. State Indicator

The status pill in the header shows:
- `● ONLINE` (green) — session connected
- `○ SLEEPING` (muted) — mic gated
- `● LISTENING` (green) — active, mic open
- `◈ THINKING` (gold, blinking) — processing
- `● SPEAKING` (orange) — TTS playing
- `⊘ MUTED` (red) — manually muted

---

## 8. Overlays / Panels

All overlays are children of the central widget positioned by hand (not in a layout). They use:
- `rgba(0, 8, 20, 248)` background — very dark blue, near-opaque
- `1px solid {BORDER_B}` border
- `border-radius: 6px`
- Fixed width (420–520px), auto-height

### _HudOverlay base class

All overlays extend `_HudOverlay` which overrides `hideEvent`/`closeEvent` to repaint the parent behind them — preventing ghost rendering after they close.

---

## 9. Audio-Reactive Design Rules

1. The orb must NEVER use a constant looping animation for "speaking"
2. The orb MUST respond to actual audio amplitude data
3. Smoothing must make animation feel cinematic (not jittery)
4. Listening and Speaking must look visually different
5. Sleeping must be nearly still

---

## 10. Accessibility

- All buttons: `setCursor(Qt.CursorShape.PointingHandCursor)`
- Keyboard shortcuts: F4 (mute), F11 (fullscreen), Escape (interrupt)
- Log widget: scrollable, readable contrast
- Status text: high contrast on dark background
- Modal overlays: Cancel/Close as default action (not destructive)

---

## 11. Web Dashboard Design

The remote dashboard (`dashboard/static/app.html`) uses:
- Fonts: Orbitron (headings), Rajdhani (body), Share Tech Mono (code/data)
- Colors: same JARVIS palette adapted to CSS custom properties
- Background canvas: particle/grid animation
- Scanlines overlay for CRT aesthetic
- Glassmorphism panels for controls
