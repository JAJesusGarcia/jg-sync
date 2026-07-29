import { create } from "zustand";
import type { EngineSnapshot } from "../types/engine";

interface EngineStore extends EngineSnapshot {
  updateSnapshot: (snapshot: Partial<EngineSnapshot>) => void;
  reset: () => void;
}

const INITIAL_STATE: EngineSnapshot = {
  bpm: 0,
  confidence: 0,
  audioLevel: 0,
  state: "CALIBRATING",
  beatDetected: true,
  connected: false,
};

export const useEngineStore = create<EngineStore>((set) => ({
  ...INITIAL_STATE,

  updateSnapshot: (snapshot) =>
    set((currentState) => ({
      ...currentState,
      ...snapshot,
    })),

  reset: () => set(INITIAL_STATE),
}));