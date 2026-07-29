import { useEffect } from "react";

import { engineService } from "../services/engine/EngineService";
import { useEngineStore } from "../store/engine";

export function useEngineRuntime() {
  const updateSnapshot = useEngineStore(
    (store) => store.updateSnapshot,
  );

  useEffect(() => {
    let disposed = false;

    async function initialize() {
      try {
        await engineService.subscribe(
          (snapshot) => {
            if (!disposed) {
              updateSnapshot(snapshot);
            }
          },
          (error) => {
            if (!disposed) {
              console.error("Engine runtime error:", error.message);

              updateSnapshot({
                connected: false,
                state: "LOST",
                beatDetected: false,
              });
            }
          },
        );

        await engineService.start();
      } catch (error) {
        if (!disposed) {
          console.error("Unable to start engine runtime:", error);

          updateSnapshot({
            connected: false,
            state: "LOST",
            beatDetected: false,
          });
        }
      }
    }

    void initialize();

    return () => {
      disposed = true;

      void engineService.stop().catch((error) => {
        console.error("Unable to stop engine runtime:", error);
      });

      void engineService.unsubscribe();
    };
  }, [updateSnapshot]);
}