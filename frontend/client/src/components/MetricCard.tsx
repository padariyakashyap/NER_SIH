import type { LucideIcon } from "lucide-react";

export function MetricCard({ label, value, unit, detail, icon: Icon, tone = "blue" }: { label: string; value: string; unit?: string; detail: string; icon: LucideIcon; tone?: "blue" | "cyan" | "amber" | "red" }) {
  const tones = { blue: "text-[#3979f6] bg-[#3979f6]/10", cyan: "text-[#08a7c4] bg-[#19c8e8]/10", amber: "text-[#c88717] bg-[#f5b942]/15", red: "text-[#d74960] bg-[#e85b6b]/10" };
  return (
    <div className="group min-w-0 rounded-2xl border border-[#d7e8f1] bg-white p-4 shadow-[0_10px_30px_rgba(11,46,83,0.04)] transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_36px_rgba(11,46,83,0.09)] sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#73869f] truncate">{label}</div>
        <div className={`grid size-8 shrink-0 place-items-center rounded-lg ${tones[tone]}`}><Icon size={16} strokeWidth={1.8} /></div>
      </div>
      <div className="mt-5 flex items-baseline gap-1 overflow-hidden">
        <span className="font-mono text-2xl font-semibold tracking-[-0.06em] text-[#0a1858] sm:text-3xl truncate">{value}</span>
        {unit && <span className="shrink-0 text-xs text-[#73869f]">{unit}</span>}
      </div>
      <div className="mt-2 text-xs text-[#6d8098] truncate">{detail}</div>
    </div>
  );
}

export function SectionLabel({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) { return <div className="mb-4 flex items-center justify-between"><h2 className="text-[11px] font-mono uppercase tracking-[0.18em] text-[#496986]">{children}</h2>{action}</div>; }
