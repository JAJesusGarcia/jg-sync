interface FooterProps {
  connected: boolean;
}

export function Footer({ connected }: FooterProps) {
  return (
    <footer className="flex items-center justify-between border-t border-[#262C36] pt-5 text-xs text-[#8E98A8]">
      <span>{connected ? "Engine connected" : "Engine disconnected"}</span>
      <span>v0.4 Visual Monitor</span>
    </footer>
  );
}