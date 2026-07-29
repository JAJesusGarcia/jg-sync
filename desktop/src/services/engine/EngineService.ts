import { invoke } from "@tauri-apps/api/core";
import {
  listen,
  type UnlistenFn,
} from "@tauri-apps/api/event";

import type {
  EngineError,
  EngineSnapshot,
} from "../../types/engine";

type SnapshotHandler = (snapshot: EngineSnapshot) => void;
type ErrorHandler = (error: EngineError) => void;

const ENGINE_SNAPSHOT_EVENT = "engine:snapshot";
const ENGINE_ERROR_EVENT = "engine:error";

class EngineService {
  private snapshotUnlisten: UnlistenFn | null = null;
  private errorUnlisten: UnlistenFn | null = null;

  async subscribe(
    onSnapshot: SnapshotHandler,
    onError: ErrorHandler,
  ): Promise<void> {
    await this.unsubscribe();

    this.snapshotUnlisten = await listen<EngineSnapshot>(
      ENGINE_SNAPSHOT_EVENT,
      (event) => {
        onSnapshot(event.payload);
      },
    );

    this.errorUnlisten = await listen<EngineError>(
      ENGINE_ERROR_EVENT,
      (event) => {
        onError(event.payload);
      },
    );
  }

  async start(): Promise<void> {
    await invoke("start_engine_stream");
  }

  async stop(): Promise<void> {
    await invoke("stop_engine_stream");
  }

  async unsubscribe(): Promise<void> {
    this.snapshotUnlisten?.();
    this.errorUnlisten?.();

    this.snapshotUnlisten = null;
    this.errorUnlisten = null;
  }
}

export const engineService = new EngineService();