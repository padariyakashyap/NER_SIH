export type RiskCategory = "Low" | "Medium" | "High";
export type RouteGenerationStatus = "available" | "single" | "empty";

export interface GeoPoint { lat: number; lng: number; }
export interface LocationOption extends GeoPoint { name: string; region: string; }
export interface RouteOption { route_name: string; distance: number; travel_time: number; risk_score: number | null; calculated_score?: number; status?: string; provider?: string; geometry?: [number, number][]; }
export interface RouteGenerationResponse { routes: RouteOption[]; status: RouteGenerationStatus; message?: string; }
export interface RiskResponse { status: string; risk_analysis: string; overall_risk_score: number; risk_category: RiskCategory; component_scores: { accident: number; road_damage: number; landslide: number }; weights: { accident: number; road_damage: number; landslide: number }; route_recommendation: string; recommended_route: RouteOption; all_routes: RouteOption[]; disclaimer: string; origin?: LocationOption; destination?: LocationOption; route_generation?: RouteGenerationResponse; }
export interface RouteAnalysisRequest { origin: string; destination: string; origin_coords?: GeoPoint; destination_coords?: GeoPoint; route_selection: string; analysis_mode: string; }
export interface DemoAlert { type: string; severity: RiskCategory; location: string; time: string; description: string; status: string; }
export interface TransparencyModel { name: string; stage: string; description: string; tone: "cyan" | "blue" | "amber"; }
