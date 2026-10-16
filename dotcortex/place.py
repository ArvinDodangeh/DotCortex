"""Place skills with the Settings embedding model, or a ring if it is unavailable."""

from __future__ import annotations

from typing import Any

from dotcortex.layout import knn_links, ring_positions, spring_layout_2d
from dotcortex.store import nearness_text


def current_embedding_model_id() -> str:
    from deeptutor.services.embedding.config import get_embedding_config

    config = get_embedding_config()
    model = str(getattr(config, "model", "") or "").strip()
    if not model:
        return ""
    binding = str(getattr(config, "binding", "") or "").strip()
    return f"{binding}:{model}" if binding else model


async def embed_nearness(skills: list[dict[str, Any]]) -> tuple[str, dict[str, list[float]]]:
    from deeptutor.services.embedding.client import get_embedding_client

    model_id = current_embedding_model_id()
    if not model_id:
        raise RuntimeError("No embedding model is configured in Settings.")
    texts = [nearness_text(skill) or skill["id"] for skill in skills]
    vectors = await get_embedding_client().embed(texts)
    if len(vectors) != len(skills):
        raise RuntimeError("Embedding model returned the wrong number of vectors.")
    return model_id, {skill["id"]: [float(v) for v in vec] for skill, vec in zip(skills, vectors)}


def apply_positions(
    skills: list[dict[str, Any]],
    positions: dict[str, dict[str, float]],
    *,
    model_id: str,
    vectors: dict[str, list[float]] | None,
) -> None:
    for skill in skills:
        pos = positions.get(skill["id"])
        if pos is None:
            continue
        if skill.get("pinned") and isinstance(skill.get("position"), dict):
            continue
        skill["position"] = {"x": pos["x"], "y": pos["y"]}
        skill["pinned"] = False
        if vectors and skill["id"] in vectors:
            skill["vector"] = vectors[skill["id"]]
            skill["embedding_model_id"] = model_id


async def place_skills(skills: list[dict[str, Any]], *, force: bool = False) -> str:
    """Return a short status: embedded, ring, or unchanged."""

    if not skills:
        return "empty"
    pinned = {
        skill["id"]: skill["position"]
        for skill in skills
        if skill.get("pinned") and isinstance(skill.get("position"), dict) and not force
    }
    if force:
        for skill in skills:
            skill["pinned"] = False
    try:
        model_id, vectors = await embed_nearness(skills)
    except Exception:
        positions = ring_positions([skill["id"] for skill in skills])
        apply_positions(skills, positions, model_id="", vectors=None)
        for skill in skills:
            if skill["id"] in pinned:
                skill["position"] = pinned[skill["id"]]
                skill["pinned"] = True
        return "ring"
    movable = [skill["id"] for skill in skills if skill["id"] not in pinned]
    edges = [
        edge
        for edge in knn_links(vectors)
        if edge[0] in movable or edge[1] in movable
    ]
    positions = spring_layout_2d(
        [skill["id"] for skill in skills],
        edges,
        pinned=pinned,
    )
    apply_positions(skills, positions, model_id=model_id, vectors=vectors)
    for skill in skills:
        if skill["id"] in pinned:
            skill["position"] = pinned[skill["id"]]
            skill["pinned"] = True
            skill["vector"] = vectors[skill["id"]]
            skill["embedding_model_id"] = model_id
    return "embedded"


def embedding_model_changed(skills: list[dict[str, Any]]) -> bool:
    model_id = current_embedding_model_id()
    if not model_id:
        return False
    return any(skill.get("embedding_model_id") not in ("", model_id) for skill in skills)
