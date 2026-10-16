"""Map color comes from a linked DeepTutor mastery path. Missing link stays neutral."""

from __future__ import annotations


def mastery_progress(path_id: str | None) -> float | None:
    if not path_id or not str(path_id).strip():
        return None
    try:
        from deeptutor.learning.storage import LearningStore

        progress = LearningStore().load(str(path_id).strip())
    except Exception:
        return None
    if progress is None:
        return None
    levels = list(getattr(progress, "mastery_levels", {}) or {}.values())
    qualitative = list(getattr(progress, "qualitative_mastery", {}) or {}.values())
    scores = [float(value) for value in levels]
    scores.extend(1.0 if flag else 0.0 for flag in qualitative)
    if not scores:
        return 0.0
    return max(0.0, min(1.0, sum(scores) / len(scores)))
