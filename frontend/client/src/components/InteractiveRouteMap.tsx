import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import { LatLngBounds } from "leaflet";
import type { GeoPoint, LocationOption, RouteOption } from "@/types/api";

const DEFAULT_CENTER: [number, number] = [25.6, 92.3];
const COLORS = { recommended: "#19c8e8", selected: "#3979f6", alternative: "#6e9eb4", danger: "#e85b6b" };

function FitRoutes({ routes, origin, destination }: { routes: RouteOption[]; origin?: GeoPoint; destination?: GeoPoint }) {
  const map = useMap();
  useEffect(() => {
    const points: [number, number][] = [];
    routes.forEach((route) => route.geometry?.forEach((point) => { if (Number.isFinite(point[0]) && Number.isFinite(point[1])) points.push(point); }));
    if (origin && destination) points.push([origin.lat, origin.lng], [destination.lat, destination.lng]);
    if (points.length > 1) map.fitBounds(new LatLngBounds(points), { padding: [28, 28], maxZoom: 10 });
  }, [map, routes, origin, destination]);
  return null;
}

export function InteractiveRouteMap({ routes, recommendedRoute, selectedRoute, origin, destination, loading = false, error, source = "api", onSelectRoute }: { routes: RouteOption[]; recommendedRoute?: string; selectedRoute?: string; origin?: LocationOption; destination?: LocationOption; loading?: boolean; error?: string | null; source?: "demo" | "api" | "unavailable"; onSelectRoute?: (route: RouteOption) => void }) {
  const visibleRoutes = routes.filter((route) => route.geometry && route.geometry.length > 1);
  return <div className="relative h-[340px] overflow-hidden rounded-2xl border border-[#b9dce8] bg-[#dff4f8] sm:h-[410px]">
    <MapContainer center={DEFAULT_CENTER} zoom={7} scrollWheelZoom={true} zoomControl={true} className="z-0 size-full" style={{ background: "#dff4f8" }}>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <FitRoutes routes={visibleRoutes} origin={origin} destination={destination} />
      {visibleRoutes.map((route) => {
        const isSelected = selectedRoute === route.route_name;
        const isRecommended = recommendedRoute === route.route_name;
        const color = isSelected ? COLORS.selected : isRecommended ? COLORS.recommended : route.risk_score > 60 ? COLORS.danger : COLORS.alternative;
        return <Polyline key={route.route_name} positions={route.geometry!} pathOptions={{ color, weight: isSelected || isRecommended ? 6 : 3, opacity: isSelected || isRecommended ? 0.95 : 0.62, dashArray: isSelected ? undefined : "8 8" }} eventHandlers={{ click: () => onSelectRoute?.(route) }}><Tooltip sticky>{route.route_name} · {route.distance} km · risk {route.risk_score}</Tooltip></Polyline>;
      })}
      {origin && <CircleMarker center={[origin.lat, origin.lng]} radius={8} pathOptions={{ color: "#080d4d", weight: 3, fillColor: "#19c8e8", fillOpacity: 1 }}><Tooltip permanent direction="top">Origin · {origin.name}</Tooltip></CircleMarker>}
      {destination && <CircleMarker center={[destination.lat, destination.lng]} radius={8} pathOptions={{ color: "#080d4d", weight: 3, fillColor: "#e85b6b", fillOpacity: 1 }}><Tooltip permanent direction="top">Destination · {destination.name}</Tooltip></CircleMarker>}
    </MapContainer>
    <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-xl border border-white/80 bg-white/90 px-3 py-2 shadow-sm backdrop-blur"><div className="text-[10px] font-mono uppercase tracking-[0.15em] text-[#0b5f7a]">Interactive route map</div><div className="mt-1 text-[11px] text-[#71849a]">OpenStreetMap · {source === "demo" ? "sample geometry / demo data" : source === "unavailable" ? "previous response preserved" : "geometry from API response"}</div></div>
    <div className="absolute bottom-4 left-4 right-4 z-10 flex flex-wrap items-center gap-3 rounded-xl border border-white/80 bg-white/90 px-3 py-2 text-[10px] font-mono uppercase tracking-[0.08em] text-[#56708c] shadow-sm backdrop-blur"><span className="flex items-center gap-1.5"><span className="size-2 rounded-full bg-[#19c8e8]" /> recommended</span><span className="flex items-center gap-1.5"><span className="size-2 rounded-full bg-[#3979f6]" /> selected</span><span className="flex items-center gap-1.5"><span className="size-2 rounded-full bg-[#6e9eb4]" /> alternative</span><span className="flex items-center gap-1.5"><span className="size-2 rounded-full bg-[#e85b6b]" /> destination</span></div>
    {loading && <div className="absolute inset-0 z-20 grid place-items-center bg-[#07104b]/45 backdrop-blur-sm"><div className="rounded-xl border border-cyan-200/20 bg-[#080d4d]/90 px-4 py-3 text-xs font-mono uppercase tracking-[0.12em] text-cyan-100">Loading route geometry…</div></div>}
    {error && !loading && <div className="absolute inset-x-5 bottom-20 z-20 rounded-xl border border-[#f4c6cd] bg-[#fff5f6]/95 px-4 py-3 text-xs text-[#a94455] shadow-sm">{error}</div>}
    {!loading && !error && !visibleRoutes.length && <div className="absolute inset-0 z-10 grid place-items-center"><div className="rounded-xl border border-[#b9dce8] bg-white/90 px-4 py-3 text-xs text-[#637990] shadow-sm">No route geometry returned for this analysis.</div></div>}
  </div>;
}
