interface BeatPulseProps {
  active: boolean;
}

export function BeatPulse({ active }: BeatPulseProps) {
  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className={[
          "h-5 w-5 rounded-full transition-all duration-100",
          active
            ? "scale-125 bg-[#60A5FA] shadow-[0_0_24px_rgba(96,165,250,0.8)]"
            : "scale-100 bg-[#1A1F27]",
        ].join(" ")}
      />

      <span className="text-[0.65rem] font-semibold tracking-[0.24em] text-[#8E98A8]">
        BEAT
      </span>
    </div>
  );
}