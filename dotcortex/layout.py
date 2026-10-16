"""Skill-map layout: cosine k-NN, then a 2D spring.

Pinned nodes keep the position the learner dragged. Unpinned nodes move.
"""

from __future__ import annotations

import math
import random

DEFAULT_K = 2
MIN_SIM = 0.45


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    return dot / (na * nb)


def knn_links(
    vectors: dict[str, list[float]],
    *,
    k: int = DEFAULT_K,
    min_sim: float = MIN_SIM,
) -> list[tuple[str, str, float]]:
    ids = list(vectors.keys())
    pairs: dict[tuple[str, str], float] = {}
    for i, a in enumerate(ids):
        scored: list[tuple[float, str]] = []
        va = vectors[a]
        for j, b in enumerate(ids):
            if i == j:
                continue
            scored.append((cosine(va, vectors[b]), b))
        scored.sort(key=lambda item: -item[0])
        for sim, b in scored[: max(1, k)]:
            if sim < min_sim:
                continue
            key = (a, b) if a < b else (b, a)
            prev = pairs.get(key)
            if prev is None or sim > prev:
                pairs[key] = sim
    return [(a, b, sim) for (a, b), sim in pairs.items()]


def ring_positions(ids: list[str]) -> dict[str, dict[str, float]]:
    n = len(ids)
    if n == 0:
        return {}
    if n == 1:
        return {ids[0]: {"x": 0.0, "y": 0.0}}
    out: dict[str, dict[str, float]] = {}
    for index, sid in enumerate(ids):
        angle = (2 * math.pi * index) / n
        out[sid] = {
            "x": round(math.cos(angle) * 4.0, 4),
            "y": round(math.sin(angle) * 4.0, 4),
        }
    return out


def spring_layout_2d(
    node_ids: list[str],
    edges: list[tuple[str, str, float]],
    *,
    pinned: dict[str, dict[str, float]] | None = None,
    iterations: int = 60,
    seed: int = 42,
) -> dict[str, dict[str, float]]:
    """Fruchterman–Reingold in 2D. Pinned coordinates are restored after each step."""

    n = len(node_ids)
    fixed = pinned or {}
    if n == 0:
        return {}
    if n == 1:
        only = node_ids[0]
        if only in fixed:
            return {only: {"x": fixed[only]["x"], "y": fixed[only]["y"]}}
        return {only: {"x": 0.0, "y": 0.0}}

    rng = random.Random(seed)
    pos: dict[str, list[float]] = {}
    for nid in node_ids:
        if nid in fixed:
            pos[nid] = [float(fixed[nid]["x"]), float(fixed[nid]["y"])]
        else:
            pos[nid] = [rng.uniform(-1, 1), rng.uniform(-1, 1)]

    k = max(0.45, math.sqrt(4.0 / n))
    temp = 1.1
    adj: dict[str, list[tuple[str, float]]] = {nid: [] for nid in node_ids}
    for a, b, weight in edges:
        if a not in adj or b not in adj:
            continue
        adj[a].append((b, weight))
        adj[b].append((a, weight))

    for _ in range(iterations):
        disp = {nid: [0.0, 0.0] for nid in node_ids}
        for i, a in enumerate(node_ids):
            for b in node_ids[i + 1 :]:
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                dist = math.sqrt(dx * dx + dy * dy) or 1e-6
                force = (k * k) / dist
                ux, uy = dx / dist, dy / dist
                disp[a][0] += ux * force
                disp[a][1] += uy * force
                disp[b][0] -= ux * force
                disp[b][1] -= uy * force
        for a, neighbors in adj.items():
            for b, weight in neighbors:
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                dist = math.sqrt(dx * dx + dy * dy) or 1e-6
                force = (dist * dist) / k * (0.5 + float(weight))
                ux, uy = dx / dist, dy / dist
                disp[a][0] -= ux * force
                disp[a][1] -= uy * force
        for nid in node_ids:
            if nid in fixed:
                pos[nid] = [float(fixed[nid]["x"]), float(fixed[nid]["y"])]
                continue
            dx, dy = disp[nid]
            length = math.sqrt(dx * dx + dy * dy) or 1e-6
            step = min(temp, length)
            pos[nid][0] += dx / length * step
            pos[nid][1] += dy / length * step
        temp *= 0.92

    free = [nid for nid in node_ids if nid not in fixed]
    if free:
        cx = sum(pos[nid][0] for nid in free) / len(free)
        cy = sum(pos[nid][1] for nid in free) / len(free)
    else:
        cx = cy = 0.0
    out: dict[str, dict[str, float]] = {}
    for nid in node_ids:
        if nid in fixed:
            out[nid] = {"x": round(float(fixed[nid]["x"]), 4), "y": round(float(fixed[nid]["y"]), 4)}
        else:
            out[nid] = {
                "x": round((pos[nid][0] - cx) * 6.0, 4),
                "y": round((pos[nid][1] - cy) * 6.0, 4),
            }
    return out
