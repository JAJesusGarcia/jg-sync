export type EngineState =
  | "CALIBRATING"
  | "TRACKING"
  | "LOCKED"
  | "LOST";

export interface EngineSnapshot {
  bpm: number;
  confidence: number;
  audioLevel: number;
  state: EngineState;
  beatDetected: boolean;
  connected: boolean;
    timestamp?: number;
}

export interface EngineError {
  message: string;
}