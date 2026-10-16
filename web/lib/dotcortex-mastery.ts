/** Active pinned mastery path — shared by map overlay and chat prefix. */

export const ACTIVE_MASTERY_KEY = "dotcortex.activeMasteryPath";

export interface ActiveMasteryPath {
  path_id: string;
  name: string;
  goal?: string;
  emoji?: string;
}

export function writeActiveMastery(path: ActiveMasteryPath | null): void {
  if (typeof window === "undefined") return;
  if (!path?.path_id) {
    window.localStorage.removeItem(ACTIVE_MASTERY_KEY);
    return;
  }
  window.localStorage.setItem(ACTIVE_MASTERY_KEY, JSON.stringify(path));
  window.dispatchEvent(new Event("dotcortex-mastery-change"));
}

export function readActiveMastery(): ActiveMasteryPath | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(ACTIVE_MASTERY_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as ActiveMasteryPath;
    if (!parsed?.path_id || !parsed.name) return null;
    return parsed;
  } catch {
    return null;
  }
}

/** Wire-only prefix. The chat bubble still shows the learner's own words. */
export function withMasteryPrefix(content: string): string {
  const path = readActiveMastery();
  if (!path) return content;
  const lines = [
    "[DotCortex mastery — stay on this path unless the learner changes it]",
    `Path: ${path.name}`,
    `path_id: ${path.path_id}`,
    path.goal ? `Goal: ${path.goal}` : "",
    "Learner message:",
    content,
  ];
  return lines.filter(Boolean).join("\n");
}
