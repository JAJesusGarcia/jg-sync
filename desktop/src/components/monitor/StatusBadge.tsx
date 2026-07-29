import type { EngineState } from "../../types/engine";

interface StatusBadgeProps {
  state: EngineState;
}

const STATUS_CONFIG: Record<
  EngineState,
  {
    label: string;
    color: string;
  }
> = {
  CALIBRATING: {
    label: "CALIBRATING",
    color: "#60A5FA",
  },
  TRACKING: {
    label: "TRACKING",
    color: "#FBBF24",
  },
  LOCKED: {
    label: "LOCKED",
    color: "#22C55E",
  },
  LOST: {
    label: "LOST",
    color: "#EF4444",
  },
};

export function StatusBadge({ state }: StatusBadgeProps) {
  const config = STATUS_CONFIG[state];

  return (
    <div
      className="flex items-center gap-2 text-sm font-medium"
      style={{ color: config.color }}
    >
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: config.color }}
      />

      {config.label}
    </div>
  );
}