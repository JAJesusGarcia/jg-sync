import { create } from "zustand";
import type { EngineSnapshot } from "../types/engine";

interface EngineStore extends EngineSnapshot {
  updateSnapshot: (snapshot: Partial<EngineSnapshot>) => void;
  reset: () => void;
}

const INITIAL_STATE: EngineSnapshot = {
  bpm: 128.46,
  confidence: 87,
  audioLevel: 64,
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