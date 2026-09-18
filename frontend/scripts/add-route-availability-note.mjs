import fs from 'node:fs';
const file = '/home/ubuntu/ner-logiai/client/src/pages/RouteAnalysis.tsx';
let text = fs.readFileSync(file, 'utf8');
const needle = '<RouteTable routes={response.all_routes} selected={selected.route_name} onSelect={(route) => { setSelected(route); toast.message(`${route.route_name} selected`); }}/><div className="mt-4 rounded-xl border border-[#bfe6ef]';
const replacement = '<RouteTable routes={response.all_routes} selected={selected.route_name} onSelect={(route) => { setSelected(route); toast.message(`${route.route_name} selected`); }}/>{response.route_generation?.status === "single" && <div className="mt-4 rounded-xl border border-[#f2dfb2] bg-[#fffaf0] px-4 py-3 text-xs text-[#80601c]">Only one route alternative was returned by the routing service.</div>}<div className="mt-4 rounded-xl border border-[#bfe6ef]';
if (!text.includes(needle)) throw new Error('route table anchor not found');
text = text.replace(needle, replacement);
fs.writeFileSync(file, text);
