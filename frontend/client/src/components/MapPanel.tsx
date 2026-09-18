import type { LocationOption, RouteOption } from "@/types/api";
import { InteractiveRouteMap } from "@/components/InteractiveRouteMap";

export function MapPanel({ routes = [], recommendedRoute, selectedRoute, origin, destination, loading = false, error, source, onSelectRoute }: { routes?: RouteOption[]; recommendedRoute?: string; selectedRoute?: string; origin?: LocationOption; destination?: LocationOption; loading?: boolean; error?: string | null; source?: "demo" | "api" | "unavailable"; onSelectRoute?: (route: RouteOption) => void }) {
  return <InteractiveRouteMap routes={routes} recommendedRoute={recommendedRoute} selectedRoute={selectedRoute} origin={origin} destination={destination} loading={loading} error={error} source={source} onSelectRoute={onSelectRoute} />;
}
