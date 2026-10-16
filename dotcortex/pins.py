"""Pinned mastery paths — DotCortex overview map source of truth."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import Any, Literal

from deeptutor.services.path_service import get_path_service

_LOCK = threading.Lock()
PinSource = Literal["user", "agent"]


def pins_path() -> Path:
    root = get_path_service().get_settings_dir().parent / "dotcortex"
    root.mkdir(parents=True, exist_ok=True)
    return root / "pins.json"


def _blank() -> dict[str, Any]:
    return {"active_path_id": None, "pins": []}


def _read() -> dict[str, Any]:
    path = pins_path()
    if not path.exists():
        return _blank()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _blank()
    if not isinstance(payload, dict):
        return _blank()
    pins = payload.get("pins")
    if not isinstance(pins, list):
        pins = []
    clean: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in pins:
        if not isinstance(row, dict):
            continue
        path_id = str(row.get("path_id") or "").strip()
        if not path_id or path_id in seen:
            continue
        seen.add(path_id)
        source = row.get("source") if row.get("source") in ("user", "agent") else "user"
        position = row.get("position")
        pos = None
        if isinstance(position, dict):
            try:
                pos = {"x": float(position.get("x", 0)), "y": float(position.get("y", 0))}
            except (TypeError, ValueError):
                pos = None
        clean.append(
            {
                "path_id": path_id,
                "source": source,
                "pinned_at": float(row.get("pinned_at") or time.time()),
                "position": pos,
            }
        )
    active = payload.get("active_path_id")
    active_id = str(active).strip() if active else None
    if active_id and active_id not in seen:
        active_id = clean[0]["path_id"] if clean else None
    return {"active_path_id": active_id, "pins": clean}


def _write(payload: dict[str, Any]) -> None:
    path = pins_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".pins.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def get_state() -> dict[str, Any]:
    with _LOCK:
        return _read()


def list_pins() -> list[dict[str, Any]]:
    return list(get_state()["pins"])


def active_path_id() -> str | None:
    return get_state().get("active_path_id")


def pin_path(path_id: str, *, source: PinSource = "user", make_active: bool = True) -> dict[str, Any]:
    path_id = str(path_id or "").strip()
    if not path_id:
        raise ValueError("path_id is required")
    with _LOCK:
        state = _read()
        pins = state["pins"]
        existing = next((row for row in pins if row["path_id"] == path_id), None)
        if existing is None:
            pins.append(
                {
                    "path_id": path_id,
                    "source": source,
                    "pinned_at": time.time(),
                    "position": None,
                }
            )
        else:
            existing["source"] = source
            existing["pinned_at"] = time.time()
        if make_active or not state.get("active_path_id"):
            state["active_path_id"] = path_id
        state["pins"] = pins
        _write(state)
        return state


def unpin_path(path_id: str) -> dict[str, Any]:
    path_id = str(path_id or "").strip()
    with _LOCK:
        state = _read()
        state["pins"] = [row for row in state["pins"] if row["path_id"] != path_id]
        if state.get("active_path_id") == path_id:
            state["active_path_id"] = state["pins"][0]["path_id"] if state["pins"] else None
        _write(state)
        return state


def set_active(path_id: str | None) -> dict[str, Any]:
    with _LOCK:
        state = _read()
        if path_id is None or not str(path_id).strip():
            state["active_path_id"] = None
            _write(state)
            return state
        path_id = str(path_id).strip()
        if not any(row["path_id"] == path_id for row in state["pins"]):
            state["pins"].append(
                {
                    "path_id": path_id,
                    "source": "user",
                    "pinned_at": time.time(),
                    "position": None,
                }
            )
        state["active_path_id"] = path_id
        _write(state)
        return state


def set_position(path_id: str, x: float, y: float) -> dict[str, Any]:
    path_id = str(path_id or "").strip()
    with _LOCK:
        state = _read()
        for row in state["pins"]:
            if row["path_id"] == path_id:
                row["position"] = {"x": float(x), "y": float(y)}
                break
        _write(state)
        return state
