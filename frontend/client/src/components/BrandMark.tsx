import { RadioTower } from "lucide-react";

export function BrandMark({ dark = true }: { dark?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative grid size-10 place-items-center rounded-xl border border-cyan-300/30 bg-cyan-300/10 text-cyan-300 shadow-[0_0_24px_rgba(25,200,232,0.16)]">
        <RadioTower size={20} strokeWidth={1.8} />
        <span className="absolute -right-1 -top-1 size-2 rounded-full bg-cyan-300 shadow-[0_0_10px_rgba(25,200,232,0.9)]" />
      </div>
      <div className="leading-none">
        <div className={`text-[17px] font-semibold tracking-[-0.03em] ${dark ? "text-white" : "text-[#0b1859]"}`}>NER-Logi<span className="text-cyan-500">AI</span></div>
        <div className={`mt-1 text-[9px] font-mono uppercase tracking-[0.18em] ${dark ? "text-slate-400" : "text-slate-500"}`}>regional intelligence</div>
      </div>
    </div>
  );
}
