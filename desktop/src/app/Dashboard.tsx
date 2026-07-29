import { AudioMeter } from "../components/monitor/AudioMeter";
import { BeatPulse } from "../components/monitor/BeatPulse";
import { BpmDisplay } from "../components/monitor/BpmDisplay";
import { ConfidenceBar } from "../components/monitor/ConfidenceBar";

export function Dashboard() {
  return (
    <section className="flex min-h-[420px] flex-col items-center justify-center">
      <div className="relative">
        <BpmDisplay value={128.46} />

        <div className="absolute -right-20 top-1/2 -translate-y-1/2">
          <BeatPulse active />
          {/* <BeatPulse active={false} /> */}
        </div>
      </div>

      <div className="mt-12 flex w-full flex-col items-center gap-8 px-6">
        <ConfidenceBar value={87} />
        <AudioMeter level={64} />
      </div>
    </section>
  );
}