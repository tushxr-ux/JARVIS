"""
tools/antigravity_controller.py
Phase 1 — Antigravity Coding Agent

Thin wrapper around the `antigravity-ide chat` CLI.
All heavier orchestration lives in coding_orchestrator.py.

CLI surface discovered:
  antigravity-ide.exe [path]           → open workspace
  antigravity-ide.exe chat [prompt]    → send prompt (mode: ask|edit|agent)
  antigravity-ide.exe chat --mode agent --add-file <path> [prompt]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# ── Find the CLI binary once ─────────────────────────────────────────────────
_AGY_CANDIDATES = [
    # Windows default install location
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Antigravity IDE" / "bin" / "antigravity-ide.cmd",
    # PATH fallback
    shutil.which("antigravity-ide") or "",
    shutil.which("agy") or "",
]
_AGY_CMD: Optional[str] = next(
    (str(p) for p in _AGY_CANDIDATES if p and Path(p).exists()), None
)

# ── Model routing table (Phase 6) ────────────────────────────────────────────
# ponytail: simple dict — no class, no registry, edit here when names change
MODELS = {
    "fast":         "claude-3-5-haiku",
    "smart":        "claude-3-5-sonnet",
    "strongest":    "claude-3-opus",
    "gemini":       "gemini-2.5-pro",
    "gemini-flash": "gemini-2.0-flash",
    "claude":       "claude-3-5-sonnet",
    "default":      "gemini-2.5-pro",
}

TASK_MODEL_MAP = {
    "BUILD":     "strongest",
    "MODIFY":    "smart",
    "DEBUG":     "smart",
    "REFACTOR":  "smart",
    "REVIEW":    "fast",
    "TEST":      "fast",
    "UPGRADE":   "smart",
    "DOCUMENT":  "fast",
    "ARCHITECT": "strongest",
}


def is_available() -> bool:
    """Return True if Antigravity IDE CLI is found on this machine."""
    return _AGY_CMD is not None


def get_cmd() -> str:
    if not _AGY_CMD:
        raise RuntimeError(
            "Antigravity IDE not found. "
            "Install from https://antigravity.dev and ensure the bin/ directory is on PATH."
        )
    return _AGY_CMD


def open_workspace(path: str | Path, new_window: bool = False) -> dict:
    """Open a folder/workspace in Antigravity IDE."""
    path = Path(path)
    args = [get_cmd(), str(path)]
    if new_window:
        args.append("--new-window")
    result = subprocess.run(args, capture_output=True, text=True, timeout=15)
    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def send_prompt(
    prompt: str,
    workspace: Optional[str | Path] = None,
    mode: str = "agent",
    extra_files: Optional[list[str]] = None,
    timeout: int = 300,
) -> dict:
    """
    Send a prompt to Antigravity via the chat CLI.
    Returns dict with ok, stdout, stderr, duration_s.
    """
    cmd = get_cmd()
    args = [cmd]
    if workspace:
        args += [str(workspace), "--reuse-window"]
    args += ["chat", "--mode", mode]
    for f in (extra_files or []):
        args += ["--add-file", f]
    args.append(prompt)

    t0 = time.monotonic()
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(workspace) if workspace else None,
        )
        elapsed = round(time.monotonic() - t0, 1)
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "duration_s": elapsed,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": f"Timed out after {timeout}s", "duration_s": timeout}
    except Exception as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc), "duration_s": 0}


def resolve_model(task_type: str = "BUILD", preference: str = "") -> str:
    """
    Return the model identifier for a given task type or user preference.
    preference overrides task_type if it matches a known key.
    """
    pref = preference.lower().strip()
    if pref:
        # Try direct match or fuzzy match
        for key in MODELS:
            if key in pref:
                return MODELS[key]
    # Fall back to task-type routing
    bucket = TASK_MODEL_MAP.get(task_type.upper(), "default")
    return MODELS.get(bucket, MODELS["default"])
