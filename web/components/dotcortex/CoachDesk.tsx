"use client";

import ChatWorkspace from "@/features/chat/components/ChatWorkspace";

/** Home: chat full-width. Map popup comes from DotCortexChrome in the workspace layout. */
export function CoachDesk() {
  return (
    <div className="relative flex h-full min-h-0 w-full">
      <div className="min-w-0 flex-1">
        <ChatWorkspace />
      </div>
    </div>
  );
}
