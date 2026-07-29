import { BpmDisplay } from "../components/monitor/BpmDisplay";
import { ConfidenceBar } from "../components/monitor/ConfidenceBar";

export function Dashboard() {
  return (
    <section className="flex min-h-[420px] flex-col items-center justify-center">
      <BpmDisplay value={0} />

      <div className="w-full px-6">
        <ConfidenceBar value={0} />
      </div>
    </section>
  );
}