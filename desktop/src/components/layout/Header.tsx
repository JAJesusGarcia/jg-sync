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

      <div className="flex items-center gap-2 text-sm font-medium text-[#60A5FA]">
        <span className="h-2 w-2 rounded-full bg-current" />
        CALIBRATING
      </div>
    </header>
  );
}