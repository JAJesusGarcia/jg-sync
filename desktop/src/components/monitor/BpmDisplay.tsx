interface BpmDisplayProps {
  value: number;
}

export function BpmDisplay({ value }: BpmDisplayProps) {
  const formattedValue = value.toFixed(2).padStart(6, "0");

  return (
    <div className="flex flex-col items-center justify-center">
      <p className="text-[clamp(5rem,18vw,9rem)] font-semibold leading-none tracking-[-0.07em] tabular-nums">
        {formattedValue}
      </p>

      <p className="mt-4 text-sm font-medium tracking-[0.3em] text-[#8E98A8]">
        BPM
      </p>
    </div>
  );
}
