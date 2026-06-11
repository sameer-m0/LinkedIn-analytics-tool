import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { ComparisonMode, RangePreset } from "../types";
import type { RangeQuery } from "../services/api";

interface RangeState {
  preset: RangePreset;
  compare: ComparisonMode;
  start?: string;
  end?: string;
  setPreset: (p: RangePreset) => void;
  setCompare: (c: ComparisonMode) => void;
  setCustom: (start: string, end: string) => void;
  query: RangeQuery;
}

const RangeContext = createContext<RangeState | null>(null);

export function RangeProvider({ children }: { children: ReactNode }) {
  const [preset, setPreset] = useState<RangePreset>("last_30");
  const [compare, setCompare] = useState<ComparisonMode>("previous_period");
  const [start, setStart] = useState<string>();
  const [end, setEnd] = useState<string>();

  const query = useMemo<RangeQuery>(
    () => ({ preset, compare, start: preset === "custom" ? start : undefined, end: preset === "custom" ? end : undefined }),
    [preset, compare, start, end],
  );

  const value: RangeState = {
    preset, compare, start, end, setPreset, setCompare, query,
    setCustom: (s, e) => { setStart(s); setEnd(e); setPreset("custom"); },
  };
  return <RangeContext.Provider value={value}>{children}</RangeContext.Provider>;
}

export function useRange(): RangeState {
  const ctx = useContext(RangeContext);
  if (!ctx) throw new Error("useRange must be used within RangeProvider");
  return ctx;
}
