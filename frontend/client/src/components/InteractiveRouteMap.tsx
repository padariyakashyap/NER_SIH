import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import { LatLngBounds } from "leaflet";
import type { GeoPoint, LocationOption, RouteOption } from "@/types/api";

const DEFAULT_CENTER: [number, number] = [25.6, 92.3];
const COLORS = {
  recommended: "#06b6d4", // CYAN
  selected: "#2563eb",    // BLUE
  alternative: "#16a34a", // GREEN
  danger: "#e85b6b"       // RED/PINK
};

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

export function InteractiveRouteMap({
  routes,
  recommendedRoute,
  selectedRoute,
  origin,
  destination,
  loading = false,
  error,
  source = "api",
  onSelectRoute
}: {
  routes: RouteOption[];
  recommendedRoute?: string;
  selectedRoute?: string;
  origin?: LocationOption;
  destination?: LocationOption;
  loading?: boolean;
  error?: string | null;
  source?: "demo" | "api" | "unavailable";
  onSelectRoute?: (route: RouteOption) => void;
}) {
  const visibleRoutes = routes.filter((route) => route.geometry && route.geometry.length > 1);

  // Debug logging for received routes
  useEffect(() => {
    if (routes && routes.length > 0) {
      console.log(`[InteractiveRouteMap] Received ${routes.length} route(s):`, routes.map((r, i) => ({
        index: i,
        route_id: r.route_name,
        provider: r.provider || "N/A",
        geometry_points: r.geometry ? r.geometry.length : 0,
        distance_km: r.distance,
        risk_score: r.risk_score
      })));
    }
  }, [routes]);

  // Sort routes so non-selected alternative routes are drawn FIRST,
  // recommended route SECOND, and selected route LAST (on top of all polylines)
  const sortedRoutes = [...visibleRoutes].sort((a, b) => {
    const aSelected = selectedRoute === a.route_name;
    const bSelected = selectedRoute === b.route_name;
    if (aSelected && !bSelected) return 1;
    if (!aSelected && bSelected) return -1;
    const aRec = recommendedRoute === a.route_name;
    const bRec = recommendedRoute === b.route_name;
    if (aRec && !bRec) return 1;
    if (!aRec && bRec) return -1;
    return 0;
  });

  return (
    <div className="relative h-[340px] overflow-hidden rounded-2xl border border-[#b9dce8] bg-[#dff4f8] sm:h-[410px]">
      <MapContainer center={DEFAULT_CENTER} zoom={7} scrollWheelZoom={true} zoomControl={true} className="z-0 size-full" style={{ background: "#dff4f8" }}>
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitRoutes routes={visibleRoutes} origin={origin} destination={destination} />
        {sortedRoutes.map((route) => {
          const isSelected = selectedRoute === route.route_name;
          const isRecommended = recommendedRoute === route.route_name;
          const color = isSelected
            ? COLORS.selected
            : isRecommended
            ? COLORS.recommended
            : (route.risk_score !== null && route.risk_score > 60)
            ? COLORS.danger
            : COLORS.alternative;

          const weight = isSelected ? 6 : isRecommended ? 5 : 5;
          const opacity = isSelected ? 0.95 : isRecommended ? 0.90 : 0.85;

          return (
            <Polyline
              key={route.route_name}
              positions={route.geometry!}
              pathOptions={{ color, weight, opacity }}
              eventHandlers={{ click: () => onSelectRoute?.(route) }}
            >
              <Tooltip sticky>
                {route.route_name}{route.provider ? ` (${route.provider.toUpperCase()})` : ""} · {route.distance} km · {route.risk_score !== null ? `risk ${route.risk_score}` : "risk pending"}
              </Tooltip>
            </Polyline>
          );
        })}
        {origin && (
          <CircleMarker center={[origin.lat, origin.lng]} radius={8} pathOptions={{ color: "#080d4d", weight: 3, fillColor: COLORS.recommended, fillOpacity: 1 }}>
            <Tooltip permanent direction="top">Origin · {origin.name}</Tooltip>
          </CircleMarker>
        )}
        {destination && (
          <CircleMarker center={[destination.lat, destination.lng]} radius={8} pathOptions={{ color: "#080d4d", weight: 3, fillColor: COLORS.danger, fillOpacity: 1 }}>
            <Tooltip permanent direction="top">Destination · {destination.name}</Tooltip>
          </CircleMarker>
        )}
      </MapContainer>
      <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-xl border border-white/80 bg-white/90 px-3 py-2 shadow-sm backdrop-blur">
        <div className="text-[10px] font-mono uppercase tracking-[0.15em] text-[#0b5f7a]">Interactive route map</div>
        <div className="mt-1 text-[11px] text-[#71849a]">
          OpenStreetMap · {source === "demo" ? "sample geometry / demo data" : source === "unavailable" ? "previous response preserved" : "geometry from API response"}
        </div>
      </div>
      <div className="absolute bottom-4 left-4 right-4 z-10 flex flex-wrap items-center gap-3 rounded-xl border border-white/80 bg-white/90 px-3 py-2 text-[10px] font-mono uppercase tracking-[0.08em] text-[#56708c] shadow-sm backdrop-blur">
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-[#06b6d4]" /> recommended</span>
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-[#2563eb]" /> selected</span>
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-[#16a34a]" /> alternative</span>
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-[#e85b6b]" /> destination</span>
      </div>
      {loading && (
        <div className="absolute inset-0 z-20 grid place-items-center bg-[#07104b]/45 backdrop-blur-sm">
          <div className="rounded-xl border border-cyan-200/20 bg-[#080d4d]/90 px-4 py-3 text-xs font-mono uppercase tracking-[0.12em] text-cyan-100">Loading route geometry…</div>
        </div>
      )}
      {error && !loading && (
        <div className="absolute inset-x-5 bottom-20 z-20 rounded-xl border border-[#f4c6cd] bg-[#fff5f6]/95 px-4 py-3 text-xs text-[#a94455] shadow-sm">{error}</div>
      )}
      {!loading && !error && !visibleRoutes.length && (
        <div className="absolute inset-0 z-10 grid place-items-center">
          <div className="rounded-xl border border-[#b9dce8] bg-white/90 px-4 py-3 text-xs text-[#637990] shadow-sm">No route geometry returned for this analysis.</div>
        </div>
      )}
    </div>
  );
}

