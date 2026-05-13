"""
Background task runner for heavy operations (dbt runs, data exports, etc.)
Uses Python's asyncio + threading to avoid blocking the FastAPI event loop.
"""
from __future__ import annotations

import asyncio
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="bg-task")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundTask:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    status: TaskStatus = TaskStatus.PENDING
    tenant_id: Optional[UUID] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None


_tasks: dict[UUID, BackgroundTask] = {}


def get_task(task_id: UUID) -> Optional[BackgroundTask]:
    return _tasks.get(task_id)


def list_tasks(tenant_id: Optional[UUID] = None) -> list[BackgroundTask]:
    if tenant_id:
        return [t for t in _tasks.values() if t.tenant_id == tenant_id]
    return list(_tasks.values())


def submit_dbt_run(
    tenant_id: Optional[UUID] = None,
    select: Optional[str] = None,
    full_refresh: bool = False,
) -> BackgroundTask:
    task = BackgroundTask(name="dbt_run", tenant_id=tenant_id)
    _tasks[task.id] = task

    def _run():
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        try:
            cmd = ["dbt", "run", "--project-dir", "/app/dbt_project"]
            if select:
                cmd += ["--select", select]
            if full_refresh:
                cmd.append("--full-refresh")

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )
            task.completed_at = time.time()

            if proc.returncode == 0:
                task.status = TaskStatus.COMPLETED
                task.result = proc.stdout[-2000:] if len(proc.stdout) > 2000 else proc.stdout
            else:
                task.status = TaskStatus.FAILED
                task.error = proc.stderr[-2000:] if len(proc.stderr) > 2000 else proc.stderr

            logger.info(
                "dbt_run_complete",
                task_id=str(task.id),
                status=task.status,
                duration_s=round(task.completed_at - task.started_at, 2),
            )
        except subprocess.TimeoutExpired:
            task.status = TaskStatus.FAILED
            task.error = "dbt run timed out after 600s"
            task.completed_at = time.time()
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error = str(exc)[:500]
            task.completed_at = time.time()

    _executor.submit(_run)
    return task


def submit_dbt_test(tenant_id: Optional[UUID] = None) -> BackgroundTask:
    task = BackgroundTask(name="dbt_test", tenant_id=tenant_id)
    _tasks[task.id] = task

    def _run():
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        try:
            proc = subprocess.run(
                ["dbt", "test", "--project-dir", "/app/dbt_project"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            task.completed_at = time.time()

            if proc.returncode == 0:
                task.status = TaskStatus.COMPLETED
                task.result = proc.stdout[-2000:]
            else:
                task.status = TaskStatus.FAILED
                task.error = proc.stderr[-2000:]
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error = str(exc)[:500]
            task.completed_at = time.time()

    _executor.submit(_run)
    return task
