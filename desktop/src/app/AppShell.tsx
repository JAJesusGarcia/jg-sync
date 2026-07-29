import { Footer } from "../components/layout/Footer";
import { Header } from "../components/layout/Header";
// import { useEngineSimulator } from "../hooks/useEngineSimulator";
// import { useEngineConnection } from "../hooks/useEngineConnection";
import { useEngineRuntime } from "../hooks/useEngineRuntime";
import { useEngineStore } from "../store/engine";
import { Dashboard } from "./Dashboard";

export function AppShell() {
//   useEngineSimulator();
    // useEngineConnection();
    useEngineRuntime();

  const {
    bpm,
    confidence,
    audioLevel,
    state,
    beatDetected,
    connected,
  } = useEngineStore();

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0B0D10] text-[#F5F7FA]">
      <section className="w-full max-w-3xl px-8 py-12">
        <Header state={state} />

        <Dashboard
          bpm={bpm}
          confidence={confidence}
          audioLevel={audioLevel}
          beatDetected={beatDetected}
        />

        <Footer connected={connected} />
      </section>
    </main>
  );
}