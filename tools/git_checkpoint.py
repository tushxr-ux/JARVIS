"""
tools/git_checkpoint.py
Phase 8 — Git Safety / Checkpoints

Thin subprocess wrapper around git.
Never pushes to remote without explicit call.
"""
from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Optional


def _git(args: list[str], cwd: str) -> dict:
    result = subprocess.run(
        ["git"] + args,
        capture_output=True, text=True,
        cwd=cwd, timeout=30,
    )
    return {
        "ok": result.returncode == 0,
        "out": result.stdout.strip(),
        "err": result.stderr.strip(),
    }


def status(workspace: str) -> dict:
    r = _git(["status", "--porcelain"], workspace)
    return {"ok": r["ok"], "changes": r["out"], "clean": r["out"] == ""}


def checkpoint(workspace: str, message: str = "") -> dict:
    """Stage all changes and commit with a JARVIS checkpoint tag."""
    if not message:
        message = f"JARVIS checkpoint {time.strftime('%Y-%m-%d %H:%M:%S')}"
    _git(["add", "-A"], workspace)
    r = _git(["commit", "-m", message], workspace)
    if not r["ok"] and "nothing to commit" in r["out"] + r["err"]:
        return {"ok": True, "message": "Nothing to commit — working tree clean.", "sha": ""}
    # Get SHA
    sha_r = _git(["rev-parse", "--short", "HEAD"], workspace)
    return {"ok": r["ok"], "message": message, "sha": sha_r["out"], "detail": r["out"]}


def diff(workspace: str, since: Optional[str] = None) -> str:
    """Return unified diff vs HEAD (or vs a specific commit SHA)."""
    args = ["diff"] if not since else ["diff", since, "HEAD"]
    return _git(args, workspace)["out"]


def changed_files(workspace: str) -> list[str]:
    r = _git(["diff", "--name-only", "HEAD"], workspace)
    return [f for f in r["out"].splitlines() if f]


def rollback(workspace: str, target: str = "HEAD~1") -> dict:
    """Reset to target ref (default: one commit back). Does NOT push."""
    r = _git(["reset", "--hard", target], workspace)
    return {"ok": r["ok"], "detail": r["out"] or r["err"]}


def log(workspace: str, n: int = 5) -> str:
    return _git(["log", f"-{n}", "--oneline"], workspace)["out"]
