# DotCortex — locked decisions

Deduced from product talks. Do not reopen without a new decision note.

## Confirmed (2026-10-16)

1. **First screen = coach desk.** Chat is Home. No always-on skills sidebar.
2. **Sidebar = Home, Library, Settings, More.**
3. **Library = materials + your record.** Books, knowledge bases, notebooks, reading, history, journal, question bank.
4. **Mastery path = the skill.** No parallel DotCortex “skill” record. What you try to master *is* a mastery path.
5. **Pin a path** (manual or coach) when that is the active goal. Pins appear as nodes on the overview map.
6. **Map icon** opens the overview of pinned paths. Click a node → that path’s full DeepTutor mastery map, and pin chat to it.
7. **Chat context** follows the **active** pinned path (title + goal). Coach stays on it until pin changes.
8. **Task Board** stays DeepTutor’s own cards.
9. **Partners, Co-Writer, Subagents, Personas, Memory, MCP, CLI, EduHub** live under More.
10. **Progress color** on overview nodes comes from that path’s mastery summary.
11. **Coach may pin** when the learner clearly aims at an existing path (match-only in v1; no auto-create path unless we add that later).
12. **Build order:** pin store → Home chat-only → map overlay → chat prefix → coach pin tool.

## Product spine

```text
HOME = Coach (chat)
Map icon → popup (not side expand) with 3D mastery-path nodes
  → open path → DeepTutor mastery map (modules / KPs / next step)
Pin = user or agent → active path for chat
```

## Nearness text (for clustering pinned paths later)

Embed only a short card per path (Settings embedding model):

- path **name**
- **goal** + short **description**
- up to ~8 **module names** or top **knowledge-point titles**
- short **source titles** summary (attached materials), not full books

Do **not** embed: quiz scores, chat logs, full PDFs, mastery %.
Scores color the node; they do not move it.

## Explicit non-goals (now)

- Separate skill embeddings / k-NN / spring layout (dropped until multi-path layout needs polish).
- Rebuilding RAG, Reading, Mastery Study, or Partners.
- Renaming the `deeptutor` Python package.

## Already shipped (brand)

Brand name, Zehnium theme, logo assets, `dotcortex` CLI, `DOTCORTEX_HOME`, extension-first rule.
