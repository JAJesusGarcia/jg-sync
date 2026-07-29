import { useEffect } from "react";
import { checkPythonEngine } from "../lib/engineBridge";
import { useEngineStore } from "../store/engine";

export function useEngineConnection() {
  const updateSnapshot = useEngineStore((store) => store.updateSnapshot);

  useEffect(() => {
    let cancelled = false;

    async function connect() {
      try {
        const version = await checkPythonEngine();

        if (cancelled) {
          return;
        }

        console.info(`JG Sync engine bridge: ${version}`);

        updateSnapshot({
          connected: true,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        console.error("Unable to connect to Python engine:", error);

        updateSnapshot({
          connected: false,
          state: "LOST",
          beatDetected: false,
        });
      }
    }

    void connect();

    return () => {
      cancelled = true;
    };
  }, [updateSnapshot]);
}