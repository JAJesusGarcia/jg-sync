interface ConfidenceBarProps {
  value: number;
}

export function ConfidenceBar({ value }: ConfidenceBarProps) {
  const normalizedValue = Math.min(Math.max(value, 0), 100);

  return (
    <section className="w-full max-w-xl">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs font-semibold tracking-[0.24em] text-[#8E98A8]">
          CONFIDENCE
        </span>

        <span className="text-sm font-medium tabular-nums text-[#F5F7FA]">
          {normalizedValue.toFixed(0)}%
        </span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-[#1A1F27]">
        <div
          className="h-full rounded-full bg-[#60A5FA] transition-[width] duration-300 ease-out"
          style={{ width: `${normalizedValue}%` }}
        />
      </div>
    </section>
  );
}