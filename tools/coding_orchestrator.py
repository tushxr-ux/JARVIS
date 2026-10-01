"""
tools/coding_orchestrator.py
Phases 2 + 4 + 5 + 9 — Coding Orchestrator

Converts natural-language user requests into engineering tasks and drives them
through the Observe → Plan → Act → Verify loop.

Uses:
  tools/antigravity_controller.py  — Antigravity CLI
  tools/project_manager.py         — project metadata
  tools/git_checkpoint.py          — git safety
  core/task_planner.py             — task graph
  actions/browser_control.py       — browser testing (existing)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Optional

BASE_DIR = Path(__file__).resolve().parent.parent


# ── Task classifier ──────────────────────────────────────────────────────────

_TASK_KEYWORDS = {
    "BUILD":    ["build", "create", "make", "generate", "scaffold", "new", "init"],
    "MODIFY":   ["change", "update", "add", "modify", "edit", "rename", "move", "refactor"],
    "DEBUG":    ["fix", "bug", "error", "broken", "crash", "debug", "issue", "not working"],
    "REVIEW":   ["review", "audit", "check", "analyse", "analyze", "inspect", "read"],
    "TEST":     ["test", "verify", "validate", "coverage", "unit test", "e2e"],
    "UPGRADE":  ["upgrade", "migrate", "update deps", "update version", "modernize"],
    "DOCUMENT": ["document", "readme", "docs", "comment", "explain"],
}


def classify_task(request: str) -> str:
    req = request.lower()
    for task_type, keywords in _TASK_KEYWORDS.items():
        if any(kw in req for kw in keywords):
            return task_type
    return "BUILD"


# ── Prompt compiler ──────────────────────────────────────────────────────────

def compile_prompt(
    request: str,
    task_type: str,
    project: Optional[dict] = None,
    context_files: Optional[list[str]] = None,
) -> str:
    """
    Convert a raw user request into a detailed engineering prompt for Antigravity.
    Instructs the agent to IMPLEMENT, not just explain.
    """
    proj = project or {}
    proj_name   = proj.get("project", "the project")
    workspace   = proj.get("workspace", "")
    stack       = proj.get("stack", [])
    branch      = proj.get("branch", "main")
    arch        = proj.get("architecture", "")
    errors      = proj.get("known_errors", [])
    recent      = proj.get("recent_changes", "")

    stack_str   = ", ".join(stack) if stack else "infer from project files"
    errors_str  = "\n".join(f"- {e}" for e in errors) if errors else "none known"
    ctx_files   = "\n".join(f"- {f}" for f in (context_files or [])) or "none specified"
    arch_str    = arch or "infer from existing codebase"
    recent_str  = recent or "none"

    action_verb = {
        "BUILD":    "IMPLEMENT from scratch",
        "MODIFY":   "MODIFY the existing code",
        "DEBUG":    "DEBUG and FIX",
        "REVIEW":   "REVIEW and report issues",
        "TEST":     "WRITE TESTS for",
        "UPGRADE":  "UPGRADE",
        "DOCUMENT": "DOCUMENT",
    }.get(task_type, "IMPLEMENT")

    return f"""You are an expert software engineer working on: {proj_name}

## TASK TYPE: {task_type}
## USER REQUEST: {request}

## YOUR JOB
{action_verb} the following based on the user request above.
Do NOT just explain or plan — actually write the complete, working code.

## PROJECT CONTEXT
- Project: {proj_name}
- Workspace: {workspace or 'current directory'}
- Stack: {stack_str}
- Branch: {branch}
- Architecture: {arch_str}
- Recent changes: {recent_str}

## KNOWN ERRORS TO AVOID
{errors_str}

## FILES TO INSPECT FIRST
{ctx_files}

## IMPLEMENTATION REQUIREMENTS
1. Implement all requested functionality completely
2. Follow the existing project conventions and file structure
3. Use the existing stack — do not add unnecessary dependencies
4. Handle edge cases and errors appropriately
5. Ensure responsive design where applicable (mobile-first)
6. Write clean, maintainable code with meaningful variable names

## COMPLETION CRITERIA
The task is DONE only when:
- All requested features are implemented and functional
- The application starts without errors
- The UI renders correctly on desktop and mobile
- No console errors in the browser
- All requested pages/components exist and are accessible

Start immediately. Implement fully. Do not ask for clarification unless truly blocked.
"""


# ── Observe → Act → Verify loop ─────────────────────────────────────────────

def verify_files_changed(workspace: str, before_files: set[str]) -> dict:
    """Check if any files were modified after a prompt."""
    after_files = {
        str(p.relative_to(workspace))
        for p in Path(workspace).rglob("*")
        if p.is_file() and not any(
            part in p.parts for part in [".git", "node_modules", "__pycache__"]
        )
    }
    changed = after_files - before_files
    return {"ok": bool(changed), "changed": list(changed)[:20]}


def verify_server_running(url: str, timeout: int = 10) -> dict:
    """Poll a URL until it responds or timeout."""
    import urllib.request, urllib.error
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return {"ok": True, "url": url}
        except Exception:
            time.sleep(1)
    return {"ok": False, "url": url, "error": f"Did not respond within {timeout}s"}


def snapshot_files(workspace: str) -> set[str]:
    return {
        str(p.relative_to(workspace))
        for p in Path(workspace).rglob("*")
        if p.is_file() and ".git" not in str(p) and "node_modules" not in str(p)
    }


# ── Main orchestration entry point ───────────────────────────────────────────

def run_coding_task(
    request: str,
    workspace: Optional[str] = None,
    model_preference: str = "",
    speak: Optional[Callable[[str], None]] = None,
    progress: Optional[Callable[[str, str], None]] = None,
    max_fix_attempts: int = 3,
) -> dict:
    """
    Full orchestration loop:
    1. Classify request
    2. Resolve project context
    3. Git checkpoint
    4. Compile prompt
    5. Send to Antigravity
    6. Verify changes
    7. Run + test
    8. Fix detected issues
    9. Return report

    speak(text)           — JARVIS voice feedback
    progress(step, status)— UI progress panel updates
    """
    from tools.antigravity_controller import (
        is_available, open_workspace, send_prompt, resolve_model,
    )
    from tools.project_manager import get_active_project, save_project
    from tools.git_checkpoint import checkpoint, status as git_status, changed_files
    from core.task_planner import build_coding_plan, SUCCESS, FAILED

    def _say(msg: str):
        if speak:
            speak(msg)

    def _prog(step: str, st: str = "running"):
        if progress:
            progress(step, st)

    report = {
        "request": request,
        "task_type": None,
        "model": None,
        "workspace": workspace,
        "steps": [],
        "files_changed": [],
        "errors_found": [],
        "errors_fixed": [],
        "status": "RUNNING",
    }

    def step(name: str, ok: bool, detail: str = ""):
        icon = "✓" if ok else "✗"
        report["steps"].append(f"{icon} {name}" + (f" — {detail}" if detail else ""))
        _prog(name, "done" if ok else "failed")

    # ── 1. Check Antigravity is available ────────────────────────────────────
    if not is_available():
        return {**report, "status": "FAILED",
                "error": "Antigravity IDE not found. Install it first."}

    # ── 2. Resolve workspace and project ─────────────────────────────────────
    proj = get_active_project() or {}
    if workspace:
        proj["workspace"] = workspace
    elif not proj.get("workspace"):
        proj["workspace"] = str(Path.home() / "Desktop" / "JarvisProjects")
    workspace = proj["workspace"]
    Path(workspace).mkdir(parents=True, exist_ok=True)
    report["workspace"] = workspace

    # ── 3. Classify + select model ───────────────────────────────────────────
    task_type = classify_task(request)
    model = resolve_model(task_type, model_preference)
    report["task_type"] = task_type
    report["model"] = model
    step("Classify task", True, f"{task_type} → model: {model}")

    # ── 4. Build task plan ───────────────────────────────────────────────────
    plan = build_coding_plan(request, task_type)
    _say(f"Starting {task_type.lower()} task. Using {model}.")

    # ── 5. Open workspace ────────────────────────────────────────────────────
    open_workspace(workspace)
    step("Open workspace", True, workspace)

    # ── 6. Git checkpoint before changes ────────────────────────────────────
    gs = git_status(workspace)
    if gs["ok"]:
        cp = checkpoint(workspace, f"JARVIS pre-task: {request[:60]}")
        step("Git checkpoint", cp["ok"], cp.get("sha", ""))
    else:
        step("Git checkpoint", False, "no git repo — skipping")

    # ── 7. Compile + send prompt ─────────────────────────────────────────────
    file_snap = snapshot_files(workspace)
    prompt = compile_prompt(request, task_type, proj)

    _say("Sending task to Antigravity.")
    result = send_prompt(prompt, workspace, mode="agent", timeout=600)
    step("Send prompt", result["ok"],
         f"{result['duration_s']}s" + (f" | {result['stderr'][:60]}" if not result["ok"] else ""))

    # ── 8. Verify files changed ──────────────────────────────────────────────
    time.sleep(2)  # brief settle
    file_result = verify_files_changed(workspace, file_snap)
    report["files_changed"] = file_result["changed"]
    step("Verify files changed", file_result["ok"],
         f"{len(file_result['changed'])} file(s)" if file_result["ok"] else "no changes detected")

    # ── 9. Browser test (web projects only) ─────────────────────────────────
    server_url = proj.get("server", "")
    if task_type in ("BUILD", "MODIFY", "DEBUG") and not server_url:
        # Try to detect a dev server port from common config files
        pkg = Path(workspace) / "package.json"
        if pkg.exists():
            server_url = "http://localhost:5173"  # vite default
            proj["server"] = server_url

    if server_url:
        sv = verify_server_running(server_url, timeout=20)
        step("Dev server running", sv["ok"], server_url)
        if sv["ok"]:
            _say("Checking the application in the browser.")
            # Use existing browser_control.py
            try:
                sys.path.insert(0, str(BASE_DIR))
                from actions.browser_control import open_browser  # type: ignore
                open_browser({"url": server_url})
                step("Browser opened", True, server_url)
            except Exception as e:
                step("Browser opened", False, str(e)[:60])

    # ── 10. Fix loop ─────────────────────────────────────────────────────────
    fix_count = 0
    if not result["ok"] and fix_count < max_fix_attempts:
        error_msg = result.get("stderr", "")[:400]
        report["errors_found"].append(error_msg)
        _say("Detected an issue. Sending a correction to Antigravity.")
        fix_prompt = (
            f"The previous task encountered this error:\n\n{error_msg}\n\n"
            f"Diagnose the root cause and fix it. Implement the complete fix now."
        )
        fix_result = send_prompt(fix_prompt, workspace, mode="agent", timeout=300)
        fix_count += 1
        if fix_result["ok"]:
            report["errors_fixed"].append(error_msg)
            step(f"Fix attempt {fix_count}", True)
        else:
            step(f"Fix attempt {fix_count}", False, fix_result.get("stderr", "")[:60])

    # ── 11. Save project metadata ─────────────────────────────────────────────
    proj_name = proj.get("project") or Path(workspace).name
    save_project({
        "project": proj_name,
        "workspace": workspace,
        "server": server_url,
        "last_task": request,
        "task_type": task_type,
        "model": model,
        "recent_changes": ", ".join(file_result["changed"][:5]),
    })

    # ── 12. Final status ──────────────────────────────────────────────────────
    failed_steps = [s for s in report["steps"] if s.startswith("✗")]
    report["status"] = "FAILED" if failed_steps else "COMPLETED"
    _say(
        "Task complete. Everything looks good." if report["status"] == "COMPLETED"
        else "Task finished with some issues. Check the progress panel."
    )
    return report


def format_report(r: dict) -> str:
    lines = [
        f"{'='*48}",
        f"JARVIS CODING REPORT",
        f"{'='*48}",
        f"Request   : {r.get('request','')[:80]}",
        f"Task type : {r.get('task_type','')}",
        f"Model     : {r.get('model','')}",
        f"Workspace : {r.get('workspace','')}",
        f"Status    : {r.get('status','')}",
        "",
        "Steps:",
    ]
    for s in r.get("steps", []):
        lines.append(f"  {s}")
    if r.get("files_changed"):
        lines.append(f"\nFiles changed ({len(r['files_changed'])}):")
        for f in r["files_changed"][:10]:
            lines.append(f"  · {f}")
    if r.get("errors_found"):
        lines.append("\nErrors found:")
        for e in r["errors_found"]:
            lines.append(f"  ⚠ {e[:80]}")
    if r.get("errors_fixed"):
        lines.append("\nErrors fixed:")
        for e in r["errors_fixed"]:
            lines.append(f"  ✓ {e[:80]}")
    lines.append("=" * 48)
    return "\n".join(lines)
