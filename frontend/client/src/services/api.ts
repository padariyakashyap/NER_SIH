import { demoResponse, locations } from "@/data/demoData";
import type { GeoPoint, LocationOption, RiskResponse, RouteAnalysisRequest, RouteGenerationResponse, RouteOption } from "@/types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const ROUTE_GENERATION_URL = import.meta.env.VITE_ROUTE_GENERATION_URL || `${API_BASE_URL}/api/routes/calculate`;
const UNIFIED_URL = import.meta.env.VITE_ROUTE_ANALYSIS_URL || `${API_BASE_URL}/analyze-route`;
const COMBINED_RISK_URL = import.meta.env.VITE_COMBINED_RISK_URL || "http://127.0.0.1:8001/combined-risk";
const RECOMMENDATION_URL = import.meta.env.VITE_API_BASE_URL ? `${import.meta.env.VITE_API_BASE_URL}/recommend-route` : "http://127.0.0.1:8002/recommend-route";

export class ApiRequestError extends Error { constructor(message: string, public kind: "timeout" | "network" | "server" | "invalid") { super(message); this.name = "ApiRequestError"; } }
function numberValue(value: unknown, fallback = 0) { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : fallback; }
function validPoint(lat: number, lng: number) { return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180; }

function extractCoordinates(value: unknown): unknown[] {
  if (Array.isArray(value)) return value;
  if (value && typeof value === "object") {
    const obj = value as Record<string, unknown>;
    if (Array.isArray(obj.coordinates)) return obj.coordinates;
  }
  return [];
}

function point(value: unknown, order: "latlng" | "lonlat" = "lonlat"): [number, number][] | undefined {
  const coords = extractCoordinates(value);
  if (!coords.length) return undefined;
  const points = coords.map((item) => {
    if (Array.isArray(item)) {
      const first = numberValue(item[0]);
      const second = numberValue(item[1]);
      return (order === "lonlat" ? [second, first] : [first, second]) as [number, number];
    }
    const object = (item || {}) as Record<string, unknown>;
    return [numberValue(object.lat), numberValue(object.lng ?? object.lon)] as [number, number];
  }).filter(([lat, lng]) => validPoint(lat, lng));
  return points.length > 0 ? points : undefined;
}

function routeValue(value: unknown, index = 0, order: "latlng" | "lonlat" = "lonlat"): RouteOption {
  if (typeof value === "string") return { route_name: value, distance: 0, travel_time: 0, risk_score: null, status: "Recommended" };
  const route = (value || {}) as Record<string, unknown>;
  const routeOrder = String(route.coordinate_order ?? route.geometry_order ?? order) === "latlng" ? "latlng" : "lonlat";

  const rawName = route.route_name ?? route.name ?? route.route_id;
  let routeName: string;
  if (rawName !== undefined && rawName !== null) {
    const nameStr = String(rawName);
    routeName = nameStr.startsWith("route_") ? `Route ${nameStr.replace("route_", "")}` : nameStr;
  } else {
    routeName = `Route ${String.fromCharCode(65 + index)}`;
  }

  const rawDistance = route.distance ?? route.distance_km ?? (numberValue(route.distance_meters) > 0 ? numberValue(route.distance_meters) / 1000 : 0);
  const distance = Math.round(numberValue(rawDistance) * 100) / 100;

  const rawTime = route.travel_time ?? route.duration_minutes ?? route.travel_time_minutes ?? (numberValue(route.duration_seconds) > 0 ? numberValue(route.duration_seconds) / 60 : 0);
  const travelTime = Math.round(numberValue(rawTime) * 100) / 100;

  const rawRisk = route.risk_score ?? route.risk;
  const riskScore = rawRisk !== null && rawRisk !== undefined ? numberValue(rawRisk) : null;

  const provider = route.provider ? String(route.provider) : undefined;
  const status = String(route.status ?? (provider ? `Calculated via ${provider.toUpperCase()}` : "Available route"));

  return {
    route_name: routeName,
    distance,
    travel_time: travelTime,
    risk_score: riskScore,
    calculated_score: numberValue(route.calculated_score ?? route.route_score ?? route.score ?? riskScore ?? 0),
    status,
    provider,
    geometry: point(route.geometry ?? route.coordinates ?? route.route_geometry, routeOrder)
  };
}

function locationValue(value: unknown, fallback?: LocationOption): LocationOption | undefined { if (!value && fallback) return fallback; const object = (value || {}) as Record<string, unknown>; const lat = numberValue(object.lat); const lng = numberValue(object.lng ?? object.lon); if (!validPoint(lat, lng)) return fallback; return { name: String(object.name ?? fallback?.name ?? "Location"), region: String(object.region ?? fallback?.region ?? "Northeast India"), lat, lng }; }

async function postJson(url: string, body: unknown) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal
    });
    if (!response.ok) throw new ApiRequestError(response.status >= 500 ? "The analysis service returned a server error." : "The analysis service rejected the request.", "server");
    let json: unknown;
    try { json = await response.json(); } catch { throw new ApiRequestError("The analysis service returned an invalid response.", "invalid"); }
    return json;
  } catch (error) {
    if (error instanceof ApiRequestError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") throw new ApiRequestError("The request timed out. Check that the FastAPI server is running.", "timeout");
    throw new ApiRequestError("Unable to retrieve route alternatives. Please try again.", "network");
  } finally {
    window.clearTimeout(timeout);
  }
}

export function normalizeGeneratedRoutes(input: unknown): RouteGenerationResponse {
  const raw = (input || {}) as Record<string, unknown>;
  const rawRoutes = Array.isArray(raw.routes) ? raw.routes : Array.isArray(input) ? input : [];
  const order = String(raw.coordinate_order ?? raw.geometry_order ?? "lonlat") === "latlng" ? "latlng" : "lonlat";
  const routes = rawRoutes.map((route, index) => routeValue(route, index, order));
  const status = routes.length === 0 ? "empty" : routes.length === 1 ? "single" : "available";
  
  console.log(`[Frontend API] Generated ${routes.length} route(s):`, routes.map((r) => ({
    route_name: r.route_name,
    provider: r.provider || "N/A",
    distance_km: r.distance,
    geometry_points: r.geometry?.length ?? 0
  })));

  return { routes, status, message: String(raw.message ?? (status === "single" ? "Only one route alternative was returned by the routing service." : "")) };
}

export async function generateRoutes(origin: GeoPoint, destination: GeoPoint, analysisMode = "Balanced assessment"): Promise<RouteGenerationResponse & { rawJson?: unknown }> {
  if (!validPoint(origin.lat, origin.lng) || !validPoint(destination.lat, destination.lng)) {
    throw new ApiRequestError("The selected coordinates are invalid. Choose the locations again.", "invalid");
  }
  const json = await postJson(ROUTE_GENERATION_URL, {
    origin: { lat: origin.lat, lng: origin.lng },
    destination: { lat: destination.lat, lng: destination.lng },
    alternative_count: 2,
    analysis_mode: analysisMode
  });
  const result = normalizeGeneratedRoutes(json);
  if (result.status === "empty") throw new ApiRequestError("Unable to retrieve route alternatives. Please try again.", "invalid");
  return { ...result, rawJson: json };
}

export function normalizeRiskResponse(input: unknown, request?: RouteAnalysisRequest, generated?: RouteGenerationResponse): RiskResponse {
  const raw = (input || {}) as Record<string, unknown>;
  const nestedAnalysis = (raw.risk_analysis && typeof raw.risk_analysis === "object" ? raw.risk_analysis : {}) as Record<string, unknown>;
  const rawRoutes = Array.isArray(raw.all_routes) ? raw.all_routes : Array.isArray(raw.routes) ? raw.routes : generated?.routes ?? [];
  const order = String(raw.coordinate_order ?? raw.geometry_order ?? "lonlat") === "latlng" ? "latlng" : "lonlat";
  const routes = rawRoutes.map((route, index) => routeValue(route, index, order));

  const rawRec = raw.recommended_route ?? raw.route_recommendation;
  const recommendation = routeValue(rawRec);
  const recommended = routes.find((route) => route.route_name === recommendation.route_name) ?? routes[0] ?? recommendation;

  if (!routes.length || !recommended.route_name) {
    throw new ApiRequestError("The analysis service returned no usable route results.", "invalid");
  }

  console.log(`[Frontend API] Normalized ${routes.length} risk route(s):`, routes.map((r) => ({
    route_name: r.route_name,
    provider: r.provider || "N/A",
    distance_km: r.distance,
    risk_score: r.risk_score,
    geometry_points: r.geometry?.length ?? 0
  })));

  const rawComponents = (raw.component_scores && typeof raw.component_scores === "object" ? raw.component_scores : nestedAnalysis.component_scores && typeof nestedAnalysis.component_scores === "object" ? nestedAnalysis.component_scores : (recommended.risk_score !== null && typeof (rawRec as any)?.component_scores === "object" ? (rawRec as any).component_scores : (recommended as any).component_scores ?? {})) as Record<string, unknown>;
  const rawWeights = (raw.weights && typeof raw.weights === "object" ? raw.weights : (recommended as any).weights ?? {}) as Record<string, unknown>;

  const overallRisk = numberValue(raw.overall_risk_score ?? nestedAnalysis.overall_risk_score ?? raw.risk_score ?? recommended.risk_score, 0);
  const category = (raw.risk_category ?? nestedAnalysis.risk_category ?? (recommended as any).risk_category ?? (overallRisk < 35 ? "Low" : overallRisk < 65 ? "Medium" : "High")) as RiskResponse["risk_category"];

  const fallbackOrigin = locations.find((item) => item.name === request?.origin);
  const fallbackDestination = locations.find((item) => item.name === request?.destination);

  return {
    status: String(raw.status ?? "success"),
    risk_analysis: typeof raw.risk_analysis === "string" ? raw.risk_analysis : String(nestedAnalysis.summary ?? `Corridor hazard analysis calculated via ${recommended.provider?.toUpperCase() || "spatial engine"}.`),
    overall_risk_score: overallRisk,
    risk_category: category,
    component_scores: {
      accident: numberValue(rawComponents.accident ?? rawComponents.accident_risk),
      road_damage: numberValue(rawComponents.road_damage ?? rawComponents.road_damage_risk),
      landslide: numberValue(rawComponents.landslide ?? rawComponents.landslide_risk)
    },
    weights: {
      accident: numberValue(rawWeights.accident ?? rawWeights.accident_weight ?? 40),
      road_damage: numberValue(rawWeights.road_damage ?? rawWeights.road_damage_weight ?? 30),
      landslide: numberValue(rawWeights.landslide ?? rawWeights.landslide_weight ?? 30)
    },
    route_recommendation: typeof raw.route_recommendation === "string" ? raw.route_recommendation : `Recommended route: ${recommended.route_name} (${recommended.distance} km, ${Math.round(recommended.travel_time)} mins).`,
    recommended_route: recommended,
    all_routes: routes,
    disclaimer: String(raw.disclaimer ?? demoResponse.disclaimer),
    origin: locationValue(raw.origin, fallbackOrigin),
    destination: locationValue(raw.destination, fallbackDestination),
    route_generation: generated
  };
}

export async function analyzeRoute(request: RouteAnalysisRequest, demoMode = true): Promise<{ data: RiskResponse; source: "demo" | "api" }> {
  if (demoMode) {
    await new Promise((resolve) => window.setTimeout(resolve, 450));
    return { data: demoResponse, source: "demo" };
  }
  if (!request.origin_coords || !request.destination_coords) throw new ApiRequestError("Origin and destination coordinates are required.", "invalid");

  const generated = await generateRoutes(request.origin_coords, request.destination_coords, request.analysis_mode);

  if (generated.rawJson) {
    return { data: normalizeRiskResponse(generated.rawJson, request, generated), source: "api" };
  }

  try {
    const body = {
      ...request,
      origin: { name: request.origin, ...request.origin_coords },
      destination: { name: request.destination, ...request.destination_coords },
      routes: generated.routes
    };
    return { data: normalizeRiskResponse(await postJson(UNIFIED_URL, body), request, generated), source: "api" };
  } catch (error) {
    return { data: normalizeRiskResponse(generated, request, generated), source: "api" };
  }
}

export async function getCombinedRisk(body: unknown) { return normalizeRiskResponse(await postJson(COMBINED_RISK_URL, body)); }
export async function recommendRoute(body: unknown) { return normalizeRiskResponse(await postJson(RECOMMENDATION_URL, body)); }

