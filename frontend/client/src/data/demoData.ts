import type { DemoAlert, LocationOption, RiskResponse, TransparencyModel } from "@/types/api";

export const locations: LocationOption[] = [
  { name: "Guwahati", lat: 26.1445, lng: 91.7362, region: "Assam" },
  { name: "Shillong", lat: 25.5788, lng: 91.8933, region: "Meghalaya" },
  { name: "Imphal", lat: 24.817, lng: 93.9368, region: "Manipur" },
  { name: "Aizawl", lat: 23.7271, lng: 92.7176, region: "Mizoram" },
  { name: "Agartala", lat: 23.8315, lng: 91.2868, region: "Tripura" },
  { name: "Gangtok", lat: 27.3389, lng: 88.6065, region: "Sikkim" },
  { name: "Itanagar", lat: 27.0844, lng: 93.6053, region: "Arunachal Pradesh" },
  { name: "Kohima", lat: 25.6751, lng: 94.1086, region: "Nagaland" },
];

const guwahatiShillong = [[26.1445,91.7362],[26.03,91.82],[25.9,91.84],[25.78,91.88],[25.5788,91.8933]] as [number, number][];
const guwahatiShillongSouth = [[26.1445,91.7362],[26.01,91.7],[25.88,91.75],[25.7,91.82],[25.5788,91.8933]] as [number, number][];
const guwahatiShillongRisky = [[26.1445,91.7362],[26.05,91.92],[25.9,92.02],[25.72,91.96],[25.5788,91.8933]] as [number, number][];

export const demoResponse: RiskResponse = {
  status: "demo", risk_analysis: "The selected corridor shows a moderate experimental risk profile driven by road condition signals.", overall_risk_score: 41, risk_category: "Medium", component_scores: { accident: 37, road_damage: 42, landslide: 29 }, weights: { accident: 40, road_damage: 30, landslide: 30 }, route_recommendation: "Route B balances a lower risk score with a manageable travel time.",
  origin: locations[0], destination: locations[1],
  recommended_route: { route_name: "Route B", distance: 140, travel_time: 200, risk_score: 25, calculated_score: 41, status: "Recommended", geometry: guwahatiShillongSouth },
  all_routes: [
    { route_name: "Route A", distance: 120, travel_time: 180, risk_score: 40, calculated_score: 49, status: "Alternative", geometry: guwahatiShillong },
    { route_name: "Route B", distance: 140, travel_time: 200, risk_score: 25, calculated_score: 41, status: "Recommended", geometry: guwahatiShillongSouth },
    { route_name: "Route C", distance: 100, travel_time: 160, risk_score: 70, calculated_score: 63, status: "Higher risk", geometry: guwahatiShillongRisky },
  ], disclaimer: "Experimental weighted risk score. Not a validated probability of route failure.",
};

export const demoAlerts: DemoAlert[] = [
  { type: "Landslide risk", severity: "High", location: "NH-6 · Jowai corridor", time: "18 min ago", description: "Prototype terrain signal indicates elevated slope exposure near a winding section.", status: "Monitoring" },
  { type: "Road damage", severity: "Medium", location: "Guwahati → Shillong", time: "42 min ago", description: "Demo road-condition input suggests reduced surface confidence on the eastern approach.", status: "Review required" },
  { type: "Weather concern", severity: "Medium", location: "Kohima → Imphal", time: "1 hr ago", description: "Sample weather layer flags a visibility concern for the next planning window.", status: "Advisory" },
  { type: "Route disruption", severity: "Low", location: "Agartala freight ring", time: "2 hrs ago", description: "Demo disruption card for interface testing; no live incident is being asserted.", status: "Unverified" },
];

export const models: TransparencyModel[] = [
  { name: "Accident severity model", stage: "01 / SIGNAL", description: "Consumes supplied accident severity probabilities for prototype weighting.", tone: "cyan" },
  { name: "Road damage model", stage: "02 / CONDITION", description: "Represents a road-condition score supplied by the connected API or demo fixture.", tone: "blue" },
  { name: "Landslide segmentation", stage: "03 / TERRAIN", description: "Represents terrain exposure signals; segmentation quality requires further validation.", tone: "amber" },
  { name: "Combined risk engine", stage: "04 / SYNTHESIS", description: "Applies configurable weights: 40% accident, 30% road damage, 30% landslide.", tone: "cyan" },
  { name: "Route scoring engine", stage: "05 / DECISION", description: "Ranks supplied route inputs. Not live traffic optimization or a guaranteed safety decision.", tone: "blue" },
];
