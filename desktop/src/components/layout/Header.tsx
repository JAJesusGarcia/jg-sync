import { StatusBadge } from "../monitor/StatusBadge";

export function Header() {
  return (
    <header className="flex items-center justify-between border-b border-[#262C36] pb-5">
      <div>
        <p className="text-xs font-semibold tracking-[0.32em] text-[#8E98A8]">
          LIVE BPM DETECTION
        </p>

        <h1 className="mt-2 text-xl font-semibold tracking-[0.16em]">
          JG SYNC
        </h1>
      </div>

      <StatusBadge state="CALIBRATING" />
    </header>
  );
}