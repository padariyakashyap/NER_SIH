import { Info } from "lucide-react";
import type { RiskResponse } from "@/types/api";

export function RiskBars({ response, compact = false }: { response: RiskResponse; compact?: boolean }) {
  const rows = [
    { label: "Accident risk", value: response.component_scores.accident, weight: response.weights.accident, color: "#19c8e8" },
    { label: "Road damage", value: response.component_scores.road_damage, weight: response.weights.road_damage, color: "#3979f6" },
    { label: "Landslide exposure", value: response.component_scores.landslide, weight: response.weights.landslide, color: "#f5b942" },
  ];
  return <div className={compact ? "space-y-3" : "space-y-5"}>{rows.map((row) => <div key={row.label}><div className="mb-2 flex items-center justify-between gap-4"><span className="text-xs font-medium text-[#294366]">{row.label}</span><span className="font-mono text-[11px] text-[#73869f]">{row.value} <span className="text-[#a7b8c9]">/ {row.weight}%</span></span></div><div className="h-2 overflow-hidden rounded-full bg-[#e5eff4]"><div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(row.value, 100)}%`, backgroundColor: row.color }} /></div></div>)}</div>;
}

export function RiskGauge({ score }: { score: number }) {
  const degrees = Math.min(Math.max(score, 0), 100) * 3.6;
  return <div className="relative grid size-40 place-items-center rounded-full" style={{ background: `conic-gradient(#3979f6 0deg ${degrees}deg, #e7f0f4 ${degrees}deg 360deg)` }}><div className="grid size-[126px] place-items-center rounded-full bg-white text-center"><div><div className="font-mono text-4xl font-semibold tracking-[-0.08em] text-[#0a1858]">{score}</div><div className="mt-1 text-[10px] font-mono uppercase tracking-[0.16em] text-[#73869f]">risk score</div></div></div></div>;
}

export function TransparencyNote({ children }: { children: React.ReactNode }) { return <div className="mt-5 flex gap-2 rounded-xl border border-[#d8e8f1] bg-[#f6fbfd] p-3 text-[11px] leading-relaxed text-[#637990]"><Info size={14} className="mt-0.5 shrink-0 text-[#3979f6]" />{children}</div>; }
