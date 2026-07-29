function App() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0B0D10] text-[#F5F7FA]">
      <section className="w-full max-w-3xl px-8 py-12">
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

        <div className="flex min-h-[420px] flex-col items-center justify-center">
          <p className="text-[clamp(5rem,18vw,9rem)] font-semibold leading-none tracking-[-0.07em] tabular-nums">
            000.00
          </p>

          <p className="mt-4 text-sm font-medium tracking-[0.3em] text-[#8E98A8]">
            BPM
          </p>
        </div>

        <footer className="flex items-center justify-between border-t border-[#262C36] pt-5 text-xs text-[#8E98A8]">
          <span>Engine disconnected</span>
          <span>v0.4 Visual Monitor</span>
        </footer>
      </section>
    </main>
  );
}

export default App;