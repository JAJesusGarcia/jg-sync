import { Footer } from "../components/layout/Footer";
import { Header } from "../components/layout/Header";
import { Dashboard } from "./Dashboard";

export function AppShell() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0B0D10] text-[#F5F7FA]">
      <section className="w-full max-w-3xl px-8 py-12">
        <Header />
        <Dashboard />
        <Footer />
      </section>
    </main>
  );
}