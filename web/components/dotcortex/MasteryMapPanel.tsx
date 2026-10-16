"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { X } from "lucide-react";

import { apiFetch, apiUrl } from "@/shared/api/client";
import {
  fetchMasteryMap,
  fetchMasteryTopicIndex,
  type MasteryMap,
  type MasteryTopicLabel,
} from "@/lib/learning-api";
import { masteryTopicRoute, MASTERY_HOME } from "@/lib/learning-routes";
import {
  writeActiveMastery,
  type ActiveMasteryPath,
} from "@/lib/dotcortex-mastery";
import {
  MasteryForceMap,
  type MasteryGraphLink,
  type MasteryGraphNode,
} from "@/components/dotcortex/MasteryForceMap";
import { useMasteryMap } from "@/components/dotcortex/mastery-map-context";

interface PinNode {
  path_id: string;
  name: string;
  emoji: string;
  goal: string;
  exists: boolean;
  progress: number | null;
  source: string;
  active: boolean;
  position: { x: number; y: number } | null;
}

interface PinsResponse {
  active_path_id: string | null;
  pins: PinNode[];
}

function toActive(pin: PinNode): ActiveMasteryPath {
  return {
    path_id: pin.path_id,
    name: pin.name,
    goal: pin.goal,
    emoji: pin.emoji,
  };
}

/** Centered popup with 3D mastery-path nodes. Open via MasteryMapTrigger. */
export function MasteryMapPanel() {
  const { open, setOpen } = useMasteryMap();
  const [pins, setPins] = useState<PinNode[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [topics, setTopics] = useState<MasteryTopicLabel[]>([]);
  const [pickId, setPickId] = useState("");
  const [drillId, setDrillId] = useState<string | null>(null);
  const [drillMap, setDrillMap] = useState<MasteryMap | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const response = await apiFetch(apiUrl("/api/dotcortex/pins"));
    if (!response.ok) throw new Error("Could not load pinned paths");
    const body = (await response.json()) as PinsResponse;
    setPins(body.pins || []);
    setActiveId(body.active_path_id);
    const active = (body.pins || []).find((pin) => pin.path_id === body.active_path_id);
    if (active) writeActiveMastery(toActive(active));
    else if (!body.active_path_id) writeActiveMastery(null);
  }, []);

  useEffect(() => {
    void load().catch(() => {
      /* ignore until the panel is opened */
    });
  }, [load]);

  useEffect(() => {
    if (!open) return;
    void load().catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Could not load pinned paths");
    });
    void fetchMasteryTopicIndex()
      .then(setTopics)
      .catch(() => setTopics([]));
  }, [open, load]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (drillId) setDrillId(null);
        else setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, drillId]);

  useEffect(() => {
    if (!drillId) {
      setDrillMap(null);
      return;
    }
    let cancelled = false;
    void fetchMasteryMap(drillId)
      .then((result) => {
        if (!cancelled) setDrillMap(result.map);
      })
      .catch(() => {
        if (!cancelled) setDrillMap(null);
      });
    return () => {
      cancelled = true;
    };
  }, [drillId]);

  const graphNodes: MasteryGraphNode[] = useMemo(
    () =>
      pins.map((pin, index) => {
        const angle = (index / Math.max(pins.length, 1)) * Math.PI * 2;
        const base =
          pin.position != null
            ? {
                x: pin.position.x * 12,
                y: pin.position.y * 12,
                z: Math.sin(angle) * 20,
              }
            : {};
        return {
          id: pin.path_id,
          name: pin.name,
          emoji: pin.emoji,
          progress: pin.progress,
          active: pin.path_id === activeId,
          ...base,
        };
      }),
    [pins, activeId],
  );

  // Soft ring links until embed/k-NN layout lands — keeps the 3D graph readable.
  const graphLinks: MasteryGraphLink[] = useMemo(() => {
    if (pins.length < 2) return [];
    return pins.slice(0, -1).map((pin, index) => ({
      source: pin.path_id,
      target: pins[index + 1].path_id,
      score: 0.35,
    }));
  }, [pins]);

  async function pinSelected() {
    const pathId = pickId.trim();
    if (!pathId) return;
    setBusy(true);
    setError(null);
    try {
      const response = await apiFetch(apiUrl("/api/dotcortex/pins"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path_id: pathId, source: "user", make_active: true }),
      });
      if (!response.ok) throw new Error("Could not pin path");
      const body = (await response.json()) as PinsResponse;
      setPins(body.pins || []);
      setActiveId(body.active_path_id);
      const active = (body.pins || []).find((pin) => pin.path_id === body.active_path_id);
      if (active) writeActiveMastery(toActive(active));
      setPickId("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not pin path");
    } finally {
      setBusy(false);
    }
  }

  async function activate(pathId: string) {
    const pin = pins.find((row) => row.path_id === pathId);
    if (!pin) return;
    setBusy(true);
    setError(null);
    try {
      const response = await apiFetch(apiUrl("/api/dotcortex/pins/active"), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path_id: pin.path_id }),
      });
      if (!response.ok) throw new Error("Could not set active path");
      const body = (await response.json()) as PinsResponse;
      setPins(body.pins || []);
      setActiveId(body.active_path_id);
      writeActiveMastery(toActive(pin));
      setDrillId(pin.path_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not set active path");
    } finally {
      setBusy(false);
    }
  }

  async function unpin(pathId: string) {
    setBusy(true);
    try {
      const response = await apiFetch(apiUrl(`/api/dotcortex/pins/${encodeURIComponent(pathId)}`), {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Could not unpin");
      const body = (await response.json()) as PinsResponse;
      setPins(body.pins || []);
      setActiveId(body.active_path_id);
      if (drillId === pathId) setDrillId(null);
      const active = (body.pins || []).find((pin) => pin.path_id === body.active_path_id);
      writeActiveMastery(active ? toActive(active) : null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not unpin");
    } finally {
      setBusy(false);
    }
  }

  const unpinnedTopics = topics.filter(
    (topic) => !pins.some((pin) => pin.path_id === topic.path_id),
  );

  if (!open) return null;
  if (typeof document === "undefined") return null;

  return createPortal(
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 sm:p-8">
          <button
            type="button"
            className="absolute inset-0 bg-black/70"
            aria-label="Close map"
            onClick={() => {
              setDrillId(null);
              setOpen(false);
            }}
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Mastery map"
            className="relative z-10 flex h-[min(92vh,820px)] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)] shadow-2xl"
          >
            <div className="flex items-start justify-between gap-3 border-b border-[var(--border)] px-5 py-3">
              <div>
                <div className="text-[15px] font-medium text-[var(--foreground)]">
                  {drillId ? "Path map" : "Mastery map"}
                </div>
                <p className="mt-1 text-[12px] leading-relaxed text-[var(--muted-foreground)]">
                  {drillId
                    ? "What you are mastering on this path."
                    : "Pinned paths as 3D nodes. Drag to orbit · click a node to open it."}
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  if (drillId) setDrillId(null);
                  else setOpen(false);
                }}
                className="rounded-md p-1.5 text-[var(--muted-foreground)] hover:bg-[var(--muted)]"
                aria-label={drillId ? "Back to overview" : "Close map"}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {!drillId ? (
              <div className="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[1fr_240px]">
                <div className="min-h-[360px] border-b border-[var(--border)] md:border-b-0 md:border-r">
                  <MasteryForceMap
                    nodes={graphNodes}
                    links={graphLinks}
                    height="100%"
                    onNodeClick={(pathId) => void activate(pathId)}
                  />
                </div>
                <div className="flex min-h-0 flex-col gap-3 overflow-y-auto p-4">
                  <label className="block text-[11px] text-[var(--muted-foreground)]">
                    Pin a mastery path
                    <select
                      value={pickId}
                      onChange={(event) => setPickId(event.target.value)}
                      className="mt-1 w-full rounded-lg border border-[var(--border)] bg-[var(--background)] px-2 py-2 text-[13px] text-[var(--foreground)]"
                    >
                      <option value="">Choose a path…</option>
                      {unpinnedTopics.map((topic) => (
                        <option key={topic.path_id} value={topic.path_id}>
                          {topic.emoji} {topic.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    disabled={busy || !pickId}
                    onClick={() => void pinSelected()}
                    className="rounded-lg bg-[var(--primary)] px-3 py-1.5 text-[12px] text-[var(--primary-foreground)] disabled:opacity-50"
                  >
                    Pin path
                  </button>
                  <Link
                    href={MASTERY_HOME}
                    className="text-[12px] text-[var(--muted-foreground)] underline"
                  >
                    Open Mastery to create a path
                  </Link>

                  {pins.length > 0 ? (
                    <ul className="mt-2 space-y-1 border-t border-[var(--border)] pt-3 text-[12px]">
                      {pins.map((pin) => (
                        <li
                          key={pin.path_id}
                          className="flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 hover:bg-[var(--muted)]"
                        >
                          <button
                            type="button"
                            className="min-w-0 flex-1 truncate text-left text-[var(--foreground)]"
                            onClick={() => void activate(pin.path_id)}
                          >
                            {pin.emoji} {pin.name}
                            {pin.active ? " · active" : ""}
                          </button>
                          <button
                            type="button"
                            className="shrink-0 text-[var(--muted-foreground)]"
                            onClick={() => void unpin(pin.path_id)}
                          >
                            Unpin
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </div>
            ) : (
              <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-5 py-4">
                <div className="text-[14px] font-medium text-[var(--foreground)]">
                  {pins.find((pin) => pin.path_id === drillId)?.name || drillId}
                </div>
                {drillMap ? (
                  <div className="space-y-3 text-[13px]">
                    <p className="text-[var(--muted-foreground)]">
                      {drillMap.counts.mastered}/{drillMap.counts.total} mastered
                      {drillMap.due_reviews ? ` · ${drillMap.due_reviews} due` : ""}
                    </p>
                    {drillMap.modules.map((module) => (
                      <div key={module.id || module.name}>
                        <div className="font-medium text-[var(--foreground)]">
                          {module.name}
                          <span className="ml-2 font-normal text-[var(--muted-foreground)]">
                            {module.mastered}/{module.total}
                          </span>
                        </div>
                        <ul className="mt-1 space-y-0.5 text-[var(--muted-foreground)]">
                          {module.knowledge_points.slice(0, 12).map((kp) => (
                            <li key={kp.id || kp.name}>· {kp.name}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[12px] text-[var(--muted-foreground)]">Loading path map…</p>
                )}
                <Link
                  href={masteryTopicRoute(drillId)}
                  className="text-[12px] text-[var(--primary)] underline"
                >
                  Open full Mastery Study
                </Link>
              </div>
            )}

            {error ? (
              <p className="px-5 pb-3 text-[11px] text-[var(--destructive)]">{error}</p>
            ) : null}
          </div>
        </div>,
    document.body,
  );
}
