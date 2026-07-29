import { useEffect } from "react";
import { useEngineStore } from "../store/engine";
import type { EngineState } from "../types/engine";

const ENGINE_STATES: EngineState[] = [
  "CALIBRATING",
  "TRACKING",
  "LOCKED",
  "LOST",
];

export function useEngineSimulator() {
  const updateSnapshot = useEngineStore((store) => store.updateSnapshot);

  useEffect(() => {
    let beatActive = false;
    let stateIndex = 0;

    const dataInterval = window.setInterval(() => {
      beatActive = !beatActive;

      const bpmVariation = Math.random() * 0.8 - 0.4;
      const confidenceVariation = Math.random() * 8 - 4;
      const audioVariation = Math.random() * 30 - 15;

      updateSnapshot({
        bpm: 128 + bpmVariation,
        confidence: 84 + confidenceVariation,
        audioLevel: 60 + audioVariation,
        beatDetected: beatActive,
        connected: true,
      });
    }, 460);

    const stateInterval = window.setInterval(() => {
      stateIndex = (stateIndex + 1) % ENGINE_STATES.length;

      updateSnapshot({
        state: ENGINE_STATES[stateIndex],
      });
    }, 4000);

    return () => {
      window.clearInterval(dataInterval);
      window.clearInterval(stateInterval);
    };
  }, [updateSnapshot]);
}