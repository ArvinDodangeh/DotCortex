"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type MasteryMapContextValue = {
  open: boolean;
  setOpen: (open: boolean) => void;
  openMap: () => void;
};

const MasteryMapContext = createContext<MasteryMapContextValue | null>(null);

export function MasteryMapProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const openMap = useCallback(() => setOpen(true), []);
  const value = useMemo(
    () => ({ open, setOpen, openMap }),
    [open, openMap],
  );
  return (
    <MasteryMapContext.Provider value={value}>{children}</MasteryMapContext.Provider>
  );
}

export function useMasteryMap() {
  const ctx = useContext(MasteryMapContext);
  if (!ctx) {
    throw new Error("useMasteryMap must be used inside MasteryMapProvider");
  }
  return ctx;
}

/** Safe for chrome that may render outside CoachDesk. */
export function useMasteryMapOptional() {
  return useContext(MasteryMapContext);
}
