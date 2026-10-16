"use client";

import type { ReactNode } from "react";

import { MasteryMapPanel } from "@/components/dotcortex/MasteryMapPanel";
import { MasteryMapProvider } from "@/components/dotcortex/mastery-map-context";

/** Workspace chrome: mastery map context + popup for any page that shows the chat header. */
export function DotCortexChrome({ children }: { children: ReactNode }) {
  return (
    <MasteryMapProvider>
      {children}
      <MasteryMapPanel />
    </MasteryMapProvider>
  );
}
