"""Skill records for the DotCortex map. One JSON file under the runtime home."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import threading
import time
import uuid
from typing import Any

from deeptutor.services.path_service import get_path_service

_LOCK = threading.Lock()
MAX_CONCEPTS = 8


def skills_path() -> Path:
    root = get_path_service().get_settings_dir().parent / "dotcortex"
    root.mkdir(parents=True, exist_ok=True)
    return root / "skills.json"


def _read() -> list[dict[str, Any]]:
    path = skills_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(payload, dict):
        rows = payload.get("skills")
    else:
        rows = payload
    return [row for row in rows if isinstance(row, dict) and row.get("id")] if isinstance(rows, list) else []


def _write(rows: list[dict[str, Any]]) -> None:
    path = skills_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".skills.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"skills": rows}, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def list_skills() -> list[dict[str, Any]]:
    with _LOCK:
        return _read()


def get_skill(skill_id: str) -> dict[str, Any] | None:
    for row in list_skills():
        if row.get("id") == skill_id:
            return row
    return None


def _clean_concepts(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text[:80])
        if len(out) >= MAX_CONCEPTS:
            break
    return out


def nearness_text(skill: dict[str, Any]) -> str:
    concepts = " ".join(_clean_concepts(skill.get("concept_titles")))
    parts = [
        str(skill.get("title") or "").strip(),
        str(skill.get("goal") or "").strip(),
        concepts,
        str(skill.get("material_summary") or "").strip(),
    ]
    return " ".join(part for part in parts if part).strip()


def blank_skill(*, title: str, goal: str = "") -> dict[str, Any]:
    now = time.time()
    return {
        "id": uuid.uuid4().hex[:12],
        "title": title.strip()[:120],
        "goal": goal.strip()[:400],
        "concept_titles": [],
        "material_summary": "",
        "material_ids": [],
        "position": None,
        "pinned": False,
        "mastery_path_id": None,
        "embedding_model_id": "",
        "vector": [],
        "created_at": now,
        "updated_at": now,
    }


def save_all(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    with _LOCK:
        _write(rows)
        return rows


def upsert(skill: dict[str, Any]) -> dict[str, Any]:
    skill["updated_at"] = time.time()
    skill["concept_titles"] = _clean_concepts(skill.get("concept_titles"))
    with _LOCK:
        rows = _read()
        for index, row in enumerate(rows):
            if row.get("id") == skill.get("id"):
                rows[index] = skill
                _write(rows)
                return skill
        rows.append(skill)
        _write(rows)
        return skill
