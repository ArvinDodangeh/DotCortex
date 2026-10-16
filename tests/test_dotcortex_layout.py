"""DotCortex map math: similar vectors cluster, pinned nodes stay put."""

from dotcortex.layout import cosine, knn_links, spring_layout_2d
from dotcortex.store import nearness_text


def test_nearness_text_uses_card_fields_not_scores():
    text = nearness_text(
        {
            "title": "LangGraph",
            "goal": "Brief an agent to build a graph",
            "concept_titles": ["state", "nodes"],
            "material_summary": "short note",
        }
    )
    assert "LangGraph" in text
    assert "state" in text
    assert "short note" in text


def test_knn_keeps_close_pairs():
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],
        "c": [0.0, 1.0],
    }
    links = knn_links(vectors, k=1, min_sim=0.5)
    pairs = {tuple(sorted((a, b))) for a, b, _ in links}
    assert ("a", "b") in pairs
    assert cosine(vectors["a"], vectors["b"]) > cosine(vectors["a"], vectors["c"])


def test_pinned_position_survives_layout():
    positions = spring_layout_2d(
        ["a", "b", "c"],
        [("a", "b", 0.9)],
        pinned={"a": {"x": 12.0, "y": -4.0}},
    )
    assert positions["a"] == {"x": 12.0, "y": -4.0}
    assert "b" in positions and "c" in positions
