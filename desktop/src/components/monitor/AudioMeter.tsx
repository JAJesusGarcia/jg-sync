interface AudioMeterProps {
  level: number;
}

export function AudioMeter({ level }: AudioMeterProps) {
  const normalizedLevel = Math.min(Math.max(level, 0), 100);

  return (
    <section className="w-full max-w-xl">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs font-semibold tracking-[0.24em] text-[#8E98A8]">
          AUDIO INPUT
        </span>

        <span className="text-sm font-medium tabular-nums text-[#F5F7FA]">
          {normalizedLevel.toFixed(0)}%
        </span>
      </div>

      <div className="flex h-3 gap-1">
        {Array.from({ length: 20 }, (_, index) => {
          const segmentThreshold = ((index + 1) / 20) * 100;
          const isActive = normalizedLevel >= segmentThreshold;

          return (
            <span
              key={index}
              className={[
                "h-full flex-1 rounded-sm transition-opacity duration-100",
                isActive
                  ? "bg-[#60A5FA] opacity-100"
                  : "bg-[#1A1F27] opacity-70",
              ].join(" ")}
            />
          );
        })}
      </div>
    </section>
  );
}