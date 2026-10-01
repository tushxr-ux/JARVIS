"""
actions/antigravity_agent.py
JARVIS action — exposes the Antigravity coding agent to Gemini voice commands.

Gemini routes here for:
  "Build a website for a restaurant"
  "Create a React app for expense tracking"
  "Fix the login bug in my project"
  "Review the whole project"
  "Continue working on FixMate"
  "Check JARVIS health"
  "Open my last project"
  "Show project status"
  "Undo the last task changes"
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


TOOL = {
    "name": "antigravity_agent",
    "description": (
        "Controls the Antigravity IDE coding agent. Use this for any coding task: "
        "building apps, fixing bugs, reviewing code, running tests, or checking project status. "
        "Also use for: 'check JARVIS health', 'open my last project', 'show project status', "
        "'undo last task', 'what changed'."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "request": {
                "type": "STRING",
                "description": "The coding task or question from the user, verbatim.",
            },
            "workspace": {
                "type": "STRING",
                "description": "Optional absolute path to the project workspace. Leave blank to use the active project.",
            },
            "model_preference": {
                "type": "STRING",
                "description": "Optional model hint: fast, smart, strongest, gemini, claude. Leave blank for auto.",
            },
            "action": {
                "type": "STRING",
                "description": (
                    "Special action instead of a coding task. One of: "
                    "health_check, project_status, list_projects, undo_last_task, show_diff, open_workspace."
                ),
            },
        },
        "required": ["request"],
    },
    "handler": None,  # set below
}


async def antigravity_agent(
    request: str = "",
    workspace: str = "",
    model_preference: str = "",
    action: str = "",
    speak=None,
    response=None,
) -> str:
    """JARVIS action handler for Antigravity coding agent."""

    # ── Special actions ───────────────────────────────────────────────────────
    if action == "health_check" or "health" in request.lower() or "check yourself" in request.lower():
        from tools.jarvis_health import check_all, format_report
        results = check_all()
        report = format_report(results)
        if speak:
            passes = sum(1 for r in results if r["status"] == "PASS")
            speak(f"{passes} out of {len(results)} health checks passed.")
        return report

    if action == "project_status" or "project status" in request.lower():
        from tools.project_manager import get_active_project
        proj = get_active_project()
        if not proj:
            return "No active project. Start a coding task first."
        return "\n".join(f"{k}: {v}" for k, v in proj.items())

    if action == "list_projects" or "list" in request.lower() and "project" in request.lower():
        from tools.project_manager import list_projects
        projects = list_projects()
        if not projects:
            return "No projects saved yet."
        return "\n".join(f"· {p.get('project','?')} — {p.get('workspace','')}" for p in projects[:10])

    if action == "undo_last_task" or "undo" in request.lower():
        from tools.project_manager import get_active_project
        from tools.git_checkpoint import rollback, log
        proj = get_active_project()
        if not proj or not proj.get("workspace"):
            return "No active project to undo."
        ws = proj["workspace"]
        hist = log(ws, 5)
        rb = rollback(ws, "HEAD~1")
        if rb["ok"]:
            if speak:
                speak("Rolled back to the previous checkpoint.")
            return f"Rolled back successfully.\n\nRecent history:\n{hist}"
        return f"Rollback failed: {rb['detail']}"

    if action == "show_diff" or "what changed" in request.lower() or "show diff" in request.lower():
        from tools.project_manager import get_active_project
        from tools.git_checkpoint import diff
        proj = get_active_project()
        if not proj or not proj.get("workspace"):
            return "No active project."
        d = diff(proj["workspace"])
        return d[:3000] if d else "No uncommitted changes."

    if action == "open_workspace":
        from tools.antigravity_controller import open_workspace as _open, is_available
        if not is_available():
            return "Antigravity IDE not found."
        ws = workspace or (lambda p: p.get("workspace") if p else None)(
            __import__("tools.project_manager", fromlist=["get_active_project"]).get_active_project()
        )
        if not ws:
            return "No workspace specified."
        _open(ws)
        return f"Opened {ws} in Antigravity."

    # ── Coding task ───────────────────────────────────────────────────────────
    if not request.strip():
        return "Please describe what you'd like me to build or fix."

    from tools.antigravity_controller import is_available
    if not is_available():
        return (
            "Antigravity IDE is not installed or not found. "
            "Please install it from https://antigravity.dev"
        )

    # Progress updates go to JARVIS log/UI via response
    steps_log = []
    def _progress(step: str, status: str):
        steps_log.append(f"[{status.upper()}] {step}")

    if speak:
        speak(f"Starting coding task: {request[:60]}.")

    from tools.coding_orchestrator import run_coding_task, format_report
    report = run_coding_task(
        request=request,
        workspace=workspace or None,
        model_preference=model_preference,
        speak=speak,
        progress=_progress,
    )

    return format_report(report)


TOOL["handler"] = antigravity_agent
