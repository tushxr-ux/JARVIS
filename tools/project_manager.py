"""
tools/project_manager.py
Phase 7 — Project Context Manager

Persistent JSON store for active project metadata.
One file per project: ~/.jarvis_projects/<name>.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

STORE_DIR = Path.home() / ".jarvis_projects"
STORE_DIR.mkdir(exist_ok=True)
_ACTIVE_FILE = STORE_DIR / "_active.txt"


def _proj_path(name: str) -> Path:
    return STORE_DIR / f"{name.lower().replace(' ', '_')}.json"


def save_project(data: dict) -> None:
    """Save/update project metadata. `data` must have at least 'project' key."""
    name = data["project"]
    path = _proj_path(name)
    existing = load_project(name) or {}
    existing.update(data)
    existing["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    # Also set as active
    _ACTIVE_FILE.write_text(name, encoding="utf-8")


def load_project(name: str) -> Optional[dict]:
    path = _proj_path(name)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_active_project() -> Optional[dict]:
    """Return the last-used project metadata, or None."""
    if not _ACTIVE_FILE.exists():
        return None
    name = _ACTIVE_FILE.read_text(encoding="utf-8").strip()
    return load_project(name) if name else None


def list_projects() -> list[dict]:
    projects = []
    for f in STORE_DIR.glob("*.json"):
        try:
            projects.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return sorted(projects, key=lambda p: p.get("updated_at", ""), reverse=True)


def update_field(name: str, **kwargs) -> None:
    """Patch specific fields on an existing project."""
    proj = load_project(name) or {"project": name}
    proj.update(kwargs)
    save_project(proj)
