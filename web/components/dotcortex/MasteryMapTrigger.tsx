"use client";

import { Map as MapIcon } from "lucide-react";

import Tooltip from "@/shared/ui/Tooltip";
import { readActiveMastery } from "@/lib/dotcortex-mastery";
import { useMasteryMapOptional } from "@/components/dotcortex/mastery-map-context";

/** Same footprint as ChatWorkspace HeaderActionButton — sits in the header row. */
export function MasteryMapTrigger() {
  const map = useMasteryMapOptional();
  const saved = typeof window !== "undefined" ? readActiveMastery() : null;

  if (!map) {
    return (
      <Tooltip label="Mastery map (unavailable)" side="bottom">
        <button
          type="button"
          disabled
          aria-label="Mastery map"
          className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[var(--muted-foreground)] opacity-40"
        >
          <MapIcon size={16} strokeWidth={1.7} className="shrink-0" />
        </button>
      </Tooltip>
    );
  }

  return (
    <Tooltip label="Mastery map" side="bottom">
      <button
        type="button"
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          map.openMap();
        }}
        aria-label="Mastery map"
        aria-pressed={map.open}
        className={`relative inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-[background-color,color,transform] duration-150 active:scale-90 ${
          map.open
            ? "bg-[var(--primary)]/10 text-[var(--primary)]"
            : "text-[var(--muted-foreground)] hover:bg-[var(--muted)]/55 hover:text-[var(--foreground)]"
        }`}
      >
        <MapIcon size={16} strokeWidth={1.7} className="shrink-0" />
        {saved ? (
          <span className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-[var(--primary)]" />
        ) : null}
      </button>
    </Tooltip>
  );
}
