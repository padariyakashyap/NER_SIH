import { Link, useLocation } from "wouter";
import { Bell, ChevronDown, LayoutDashboard, LogOut, Menu, Mountain, Route, ShieldAlert, Sparkles, X } from "lucide-react";
import { useState } from "react";
import { BrandMark } from "@/components/BrandMark";
import { useAnalysis } from "@/contexts/AnalysisContext";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/route-analysis", label: "Route analysis", icon: Route },
  { href: "/risk-analysis", label: "Risk intelligence", icon: ShieldAlert },
  { href: "/landslide-detection", label: "Landslide Detection", icon: Mountain },
  { href: "/alerts", label: "Alerts", icon: Bell },
];

export function AppShell({ children, title, eyebrow }: { children: React.ReactNode; title: string; eyebrow: string }) {
  const [location] = useLocation();
  const [open, setOpen] = useState(false);
  const { status, lastUpdated } = useAnalysis();
  const statusTone = status === "API CONNECTED" ? "bg-[#35d6a1]" : status === "API UNAVAILABLE" ? "bg-[#e85b6b]" : status === "LOADING" ? "bg-[#f5b942]" : "bg-[#19c8e8]";
  return (
    <div className="min-h-screen bg-[#f4f9fc] text-[#102052]">
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-[248px] flex-col bg-[#080d4d] px-5 py-6 text-white transition-transform duration-200 lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex items-center justify-between">
          <Link href="/" onClick={() => setOpen(false)}><BrandMark /></Link>
          <button className="rounded-lg p-2 text-slate-400 hover:bg-white/10 lg:hidden" onClick={() => setOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <div className="mt-10 rounded-2xl border border-cyan-300/15 bg-white/[0.04] p-3">
          <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.14em] text-cyan-300"><span className={`size-1.5 ${status === "LOADING" ? "animate-pulse" : ""} rounded-full ${statusTone}`} /> {status}</div>
          <p className="mt-2 text-xs leading-relaxed text-slate-400">Prototype intelligence workspace for Northeast India logistics planning.</p>
        </div>
        <nav className="mt-8 space-y-1">
          <div className="mb-3 px-3 text-[10px] font-mono uppercase tracking-[0.2em] text-slate-500">Workspace</div>
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = location === href || (href === "/dashboard" && location === "/");
            return <Link key={href} href={href} onClick={() => setOpen(false)} className={`group flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${active ? "bg-cyan-300 text-[#07104b] shadow-[0_8px_24px_rgba(25,200,232,0.16)]" : "text-slate-300 hover:bg-white/[0.07] hover:text-white"}`}><Icon size={17} strokeWidth={1.8} /><span>{label}</span>{active && <span className="ml-auto size-1.5 rounded-full bg-[#07104b]" />}</Link>;
          })}
        </nav>
        <div className="mt-auto space-y-2">
          <Link href="/about" onClick={() => setOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-slate-300 transition hover:bg-white/[0.07] hover:text-white"><Sparkles size={17} /> Model transparency</Link>
          <div className="border-t border-white/10 pt-4">
            <div className="flex items-center gap-3 rounded-xl px-3 py-2">
              <div className="grid size-8 place-items-center rounded-full bg-gradient-to-br from-cyan-300 to-blue-500 text-xs font-semibold text-[#07104b]">DP</div>
              <div className="min-w-0"><div className="truncate text-xs font-medium">Demo planner</div><div className="text-[10px] text-slate-500">Phase 1 access</div></div>
              <ChevronDown size={15} className="ml-auto text-slate-500" />
            </div>
            <Link href="/" className="mt-2 flex items-center gap-3 rounded-xl px-3 py-2 text-xs text-slate-400 hover:bg-white/[0.07] hover:text-white"><LogOut size={15} /> Exit workspace</Link>
          </div>
        </div>
      </aside>
      {open && <button aria-label="Close menu" className="fixed inset-0 z-30 bg-[#03062d]/60 backdrop-blur-sm lg:hidden" onClick={() => setOpen(false)} />}
      <div className="lg:pl-[248px]">
        <header className="sticky top-0 z-20 border-b border-[#d8e8f2] bg-[#f4f9fc]/90 px-4 py-4 backdrop-blur-xl sm:px-6 lg:px-10">
          <div className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3"><button className="rounded-lg border border-[#d6e7f1] bg-white p-2 text-[#102052] lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu size={18} /></button><div className="min-w-0"><div className="truncate text-[10px] font-mono uppercase tracking-[0.18em] text-[#3979f6]">{eyebrow}</div><h1 className="mt-1 truncate text-xl font-semibold tracking-[-0.03em] text-[#0a1858] sm:text-2xl">{title}</h1></div></div>
            <div className="flex items-center gap-2 sm:gap-4"><div className="hidden items-center gap-2 rounded-full border border-[#cfe7f0] bg-white px-3 py-2 text-[10px] font-mono uppercase tracking-[0.12em] text-[#277c8d] sm:flex"><span className={`size-1.5 rounded-full ${statusTone}`} /> {status}{lastUpdated ? ` · updated ${lastUpdated}` : ""}</div><button className="relative grid size-9 place-items-center rounded-xl border border-[#d6e7f1] bg-white text-[#102052] transition hover:-translate-y-0.5 hover:shadow-sm" aria-label="Notifications"><Bell size={17} /><span className="absolute right-2 top-2 size-1.5 rounded-full bg-[#e85b6b]" /></button><div className="hidden size-9 place-items-center rounded-full bg-[#dff5fb] text-xs font-semibold text-[#0a5370] sm:grid">DP</div></div>
          </div>
        </header>
        <main className="mx-auto max-w-[1520px] px-4 py-6 sm:px-6 sm:py-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}
