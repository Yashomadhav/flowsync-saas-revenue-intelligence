"""Pipeline management router — trigger dbt runs, check status."""
from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from auth.dependencies import CurrentUser, require_role
from auth.models import UserRole
from services.background_tasks import (
    BackgroundTask,
    get_task,
    list_tasks,
    submit_dbt_run,
    submit_dbt_test,
)

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

AdminAuth = Annotated[CurrentUser, Depends(require_role(UserRole.ADMIN))]


def _task_to_dict(t: BackgroundTask) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "status": t.status.value,
        "started_at": t.started_at,
        "completed_at": t.completed_at,
        "duration_s": round(t.completed_at - t.started_at, 2) if t.started_at and t.completed_at else None,
        "result": t.result,
        "error": t.error,
    }


@router.post("/dbt/run", status_code=status.HTTP_202_ACCEPTED)
def trigger_dbt_run(
    user: AdminAuth,
    select: Optional[str] = None,
    full_refresh: bool = False,
) -> dict:
    task = submit_dbt_run(
        tenant_id=user.tenant_id,
        select=select,
        full_refresh=full_refresh,
    )
    return {"message": "dbt run submitted", "task": _task_to_dict(task)}


@router.post("/dbt/test", status_code=status.HTTP_202_ACCEPTED)
def trigger_dbt_test(user: AdminAuth) -> dict:
    task = submit_dbt_test(tenant_id=user.tenant_id)
    return {"message": "dbt test submitted", "task": _task_to_dict(task)}


@router.get("/tasks")
def get_pipeline_tasks(user: AdminAuth) -> list[dict]:
    tasks = list_tasks(tenant_id=user.tenant_id)
    return [_task_to_dict(t) for t in tasks]


@router.get("/tasks/{task_id}")
def get_pipeline_task(task_id: str, user: AdminAuth) -> dict:
    task = get_task(UUID(task_id))
    if not task or task.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return _task_to_dict(task)
