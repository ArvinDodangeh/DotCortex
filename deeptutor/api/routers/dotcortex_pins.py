"""DotCortex mastery-path pins API."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dotcortex.pins import (
    get_state,
    pin_path,
    set_active,
    set_position,
    unpin_path,
)
from dotcortex.progress import mastery_progress

router = APIRouter()


def _path_meta(path_id: str) -> dict[str, Any]:
    name = path_id
    emoji = "🧭"
    exists = False
    try:
        from deeptutor.learning import policy
        from deeptutor.learning.storage import LearningStore

        store = LearningStore()
        exists = store.exists(path_id)
        progress = store.load(path_id) if exists else None
        if progress is not None:
            name = policy.path_display_name(progress)
        topic = store.get_topic(path_id, progress=progress) if exists else None
        if topic is not None and getattr(topic, "metadata", None) is not None:
            emoji = getattr(topic.metadata, "emoji", None) or emoji
            goal = getattr(topic.metadata, "goal", None) or ""
        else:
            goal = ""
    except Exception:
        goal = ""
        exists = False
    return {
        "path_id": path_id,
        "name": name,
        "emoji": emoji,
        "goal": goal,
        "exists": exists,
        "progress": mastery_progress(path_id) if exists else None,
    }


def _public(state: dict[str, Any]) -> dict[str, Any]:
    pins = []
    for row in state.get("pins") or []:
        meta = _path_meta(row["path_id"])
        pins.append(
            {
                **meta,
                "source": row.get("source") or "user",
                "pinned_at": row.get("pinned_at"),
                "position": row.get("position"),
                "active": row["path_id"] == state.get("active_path_id"),
            }
        )
    active_id = state.get("active_path_id")
    active = next((pin for pin in pins if pin["path_id"] == active_id), None)
    return {"active_path_id": active_id, "active": active, "pins": pins}


class PinBody(BaseModel):
    path_id: str = Field(min_length=1, max_length=200)
    source: Literal["user", "agent"] = "user"
    make_active: bool = True


class ActiveBody(BaseModel):
    path_id: str | None = None


class PositionBody(BaseModel):
    x: float
    y: float


@router.get("/pins")
async def list_pinned() -> dict[str, Any]:
    return _public(get_state())


@router.post("/pins")
async def create_pin(body: PinBody) -> dict[str, Any]:
    path_id = body.path_id.strip()
    if not path_id:
        raise HTTPException(status_code=400, detail="path_id is required")
    try:
        from deeptutor.learning.storage import LearningStore

        if not LearningStore().exists(path_id):
            raise HTTPException(status_code=404, detail="Mastery path not found")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    state = pin_path(path_id, source=body.source, make_active=body.make_active)
    return _public(state)


@router.delete("/pins/{path_id}")
async def remove_pin(path_id: str) -> dict[str, Any]:
    return _public(unpin_path(path_id))


@router.put("/pins/active")
async def put_active(body: ActiveBody) -> dict[str, Any]:
    path_id = body.path_id.strip() if body.path_id else None
    if path_id:
        try:
            from deeptutor.learning.storage import LearningStore

            if not LearningStore().exists(path_id):
                raise HTTPException(status_code=404, detail="Mastery path not found")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    return _public(set_active(path_id))


@router.patch("/pins/{path_id}/position")
async def patch_position(path_id: str, body: PositionBody) -> dict[str, Any]:
    state = get_state()
    if not any(row["path_id"] == path_id for row in state.get("pins") or []):
        raise HTTPException(status_code=404, detail="Pin not found")
    return _public(set_position(path_id, body.x, body.y))
