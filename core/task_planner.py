"""
core/task_planner.py
Phase 3 — Agentic Task Planner

Simple dataclass-based task graph. No external dependencies.
States: PENDING RUNNING WAITING SUCCESS FAILED RETRYING BLOCKED CANCELLED
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

PENDING   = "PENDING"
RUNNING   = "RUNNING"
WAITING   = "WAITING"
SUCCESS   = "SUCCESS"
FAILED    = "FAILED"
RETRYING  = "RETRYING"
BLOCKED   = "BLOCKED"
CANCELLED = "CANCELLED"


@dataclass
class Task:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    status: str = PENDING
    owner: str = "jarvis"           # which tool/agent handles this
    depends_on: list[str] = field(default_factory=list)  # task IDs
    retry_count: int = 0
    max_retries: int = 3
    result: str = ""
    error: str = ""
    verified: bool = False
    started_at: float = 0.0
    ended_at: float = 0.0

    def start(self):
        self.status = RUNNING
        self.started_at = time.monotonic()

    def succeed(self, result: str = "", verified: bool = True):
        self.status = SUCCESS
        self.result = result
        self.verified = verified
        self.ended_at = time.monotonic()

    def fail(self, error: str = ""):
        self.error = error
        self.ended_at = time.monotonic()
        if self.retry_count < self.max_retries:
            self.status = RETRYING
            self.retry_count += 1
        else:
            self.status = FAILED

    def cancel(self):
        self.status = CANCELLED
        self.ended_at = time.monotonic()

    @property
    def duration(self) -> float:
        if self.ended_at and self.started_at:
            return round(self.ended_at - self.started_at, 1)
        return 0.0


class TaskPlan:
    """Ordered list of tasks with dependency awareness."""

    def __init__(self, goal: str = ""):
        self.goal = goal
        self.tasks: list[Task] = []

    def add(self, name: str, owner: str = "jarvis", depends_on: list[str] = None,
            max_retries: int = 3) -> Task:
        t = Task(name=name, owner=owner,
                 depends_on=depends_on or [], max_retries=max_retries)
        self.tasks.append(t)
        return t

    def get(self, task_id: str) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)

    def next_runnable(self) -> Optional[Task]:
        """Return next PENDING task whose dependencies are all SUCCESS."""
        done_ids = {t.id for t in self.tasks if t.status == SUCCESS}
        for t in self.tasks:
            if t.status == PENDING:
                if all(dep in done_ids for dep in t.depends_on):
                    return t
        return None

    def is_complete(self) -> bool:
        return all(t.status in (SUCCESS, CANCELLED) for t in self.tasks)

    def has_failed(self) -> bool:
        return any(t.status == FAILED for t in self.tasks)

    def summary(self) -> str:
        icons = {SUCCESS: "✓", FAILED: "✗", RUNNING: "↻",
                 PENDING: "○", RETRYING: "↺", CANCELLED: "⊘",
                 WAITING: "…", BLOCKED: "⛔"}
        lines = [f"Goal: {self.goal}"]
        for t in self.tasks:
            icon = icons.get(t.status, "?")
            retry = f" (retry {t.retry_count}/{t.max_retries})" if t.retry_count else ""
            lines.append(f"  {icon} {t.name}{retry}")
            if t.error:
                lines.append(f"    ⚠ {t.error[:80]}")
        return "\n".join(lines)


def build_coding_plan(goal: str, task_type: str = "BUILD") -> TaskPlan:
    """
    Generate a standard task plan for a coding goal.
    Reuses the same task sequence for all BUILD tasks.
    """
    plan = TaskPlan(goal=goal)

    t0 = plan.add("Inspect workspace",            owner="antigravity")
    t1 = plan.add("Analyze requirements",         owner="orchestrator",  depends_on=[t0.id])
    t2 = plan.add("Create git checkpoint",         owner="git",           depends_on=[t1.id])
    t3 = plan.add("Send prompt to Antigravity",   owner="antigravity",   depends_on=[t2.id], max_retries=5)
    t4 = plan.add("Verify files changed",          owner="verifier",      depends_on=[t3.id])
    t5 = plan.add("Install dependencies",          owner="dev_agent",     depends_on=[t4.id])
    t6 = plan.add("Start dev server",              owner="dev_agent",     depends_on=[t5.id])
    t7 = plan.add("Open browser + inspect UI",    owner="browser_tester",depends_on=[t6.id])
    t8 = plan.add("Check for errors",             owner="verifier",      depends_on=[t7.id])
    t9 = plan.add("Fix detected issues",           owner="antigravity",   depends_on=[t8.id], max_retries=3)
    t10= plan.add("Retest and verify",             owner="verifier",      depends_on=[t9.id])
    plan.add("Save project metadata",             owner="project_manager",depends_on=[t10.id])

    # Skip server/browser tasks for non-web project types
    if task_type in ("REVIEW", "DOCUMENT"):
        for t in [t5, t6, t7, t8, t9, t10]:
            t.status = CANCELLED

    return plan
