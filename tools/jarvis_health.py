"""
tools/jarvis_health.py
Phase 12 — Self Diagnostics

Run with: python tools/jarvis_health.py
Or call check_all() from within JARVIS.
"""
from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
API_CONFIG = BASE_DIR / "config" / "api_keys.json"


def _pass(label: str, detail: str = "") -> dict:
    return {"label": label, "status": "PASS", "detail": detail}

def _warn(label: str, detail: str) -> dict:
    return {"label": label, "status": "WARN", "detail": detail}

def _fail(label: str, detail: str, fix: str = "") -> dict:
    return {"label": label, "status": "FAIL", "detail": detail, "fix": fix}


def check_api_key() -> dict:
    try:
        data = json.loads(API_CONFIG.read_text())
        key = data.get("gemini_api_key", "")
        if key and len(key) > 10:
            return _pass("Gemini API key", "configured")
        return _fail("Gemini API key", "missing or blank", "Add key to config/api_keys.json")
    except Exception as e:
        return _fail("Gemini API key", str(e), "Ensure config/api_keys.json exists")


def check_internet() -> dict:
    try:
        socket.setdefaulttimeout(3)
        socket.create_connection(("8.8.8.8", 53))
        return _pass("Internet", "connected")
    except OSError:
        return _fail("Internet", "no connection", "Check network")


def check_microphone() -> dict:
    try:
        import sounddevice as sd  # type: ignore
        devs = sd.query_devices()
        inputs = [d for d in devs if d["max_input_channels"] > 0]
        if inputs:
            return _pass("Microphone", f"{len(inputs)} input device(s) found")
        return _warn("Microphone", "no input devices detected")
    except Exception as e:
        return _fail("Microphone", str(e), "pip install sounddevice")


def check_browser_automation() -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return _pass("Browser automation", result.stdout.strip())
        return _fail("Browser automation", "playwright not installed", "python -m playwright install chromium")
    except Exception as e:
        return _fail("Browser automation", str(e), "pip install playwright && python -m playwright install")


def check_antigravity() -> dict:
    from tools.antigravity_controller import is_available, _AGY_CMD
    if is_available():
        return _pass("Antigravity IDE", str(_AGY_CMD))
    return _warn("Antigravity IDE", "CLI not found — coding agent will be unavailable")


def check_git() -> dict:
    git = shutil.which("git")
    if git:
        r = subprocess.run(["git", "--version"], capture_output=True, text=True)
        return _pass("Git", r.stdout.strip())
    return _warn("Git", "not found — checkpoints disabled")


def check_memory() -> dict:
    mem_path = BASE_DIR / "memory" / "long_term.json"
    if mem_path.exists():
        size = mem_path.stat().st_size
        return _pass("Memory store", f"{size:,} bytes")
    return _warn("Memory store", "not yet created (first run?)")


def check_python_deps() -> dict:
    required = ["google.genai", "PyQt6", "numpy", "sounddevice"]
    missing = []
    for mod in required:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        return _fail("Python deps", f"missing: {', '.join(missing)}", "pip install -r requirements.txt")
    return _pass("Python deps", "all core deps present")


def check_all() -> list[dict]:
    checks = [
        check_api_key,
        check_internet,
        check_microphone,
        check_python_deps,
        check_browser_automation,
        check_git,
        check_memory,
        check_antigravity,
    ]
    return [c() for c in checks]


def format_report(results: list[dict]) -> str:
    icons = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}
    lines = ["JARVIS HEALTH CHECK", "─" * 40]
    for r in results:
        icon = icons.get(r["status"], "?")
        line = f"{icon} {r['label']:<28} {r['detail']}"
        lines.append(line)
        if r.get("fix"):
            lines.append(f"   → FIX: {r['fix']}")
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    lines.append("─" * 40)
    lines.append(f"{pass_count}/{len(results)} checks passed")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys as _sys
    for _s in (_sys.stdout, _sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    results = check_all()
    print(format_report(results))
