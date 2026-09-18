import { createContext, useContext, useMemo, useState } from "react";
import { demoResponse } from "@/data/demoData";
import { analyzeRoute as requestAnalysis } from "@/services/api";
import type { RiskResponse, RouteAnalysisRequest } from "@/types/api";

export type AnalysisStatus = "DEMO MODE" | "API CONNECTED" | "API UNAVAILABLE" | "LOADING";
export type ResponseSource = "demo" | "api" | "unavailable";

interface AnalysisContextValue {
  response: RiskResponse;
  source: ResponseSource;
  status: AnalysisStatus;
  demoMode: boolean;
  setDemoMode: (enabled: boolean) => void;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
  analyze: (request: RouteAnalysisRequest) => Promise<boolean>;
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const [response, setResponse] = useState<RiskResponse>(demoResponse);
  const [source, setSource] = useState<ResponseSource>("demo");
  const [demoMode, setDemoMode] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  async function analyze(request: RouteAnalysisRequest) {
    setLoading(true);
    setError(null);
    setSource(demoMode ? "demo" : "unavailable");
    try {
      const result = await requestAnalysis(request, demoMode);
      setResponse(result.data);
      setSource(result.source);
      setLastUpdated(result.source === "api" ? new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : null);
      return true;
    } catch (caught) {
      setSource("unavailable");
      setError(caught instanceof Error ? caught.message : "Unable to reach the analysis service. Check that the FastAPI server is running.");
      return false;
    } finally {
      setLoading(false);
    }
  }

  const value = useMemo<AnalysisContextValue>(() => ({ response, source, status: loading ? "LOADING" : source === "api" ? "API CONNECTED" : source === "unavailable" ? "API UNAVAILABLE" : "DEMO MODE", demoMode, setDemoMode, loading, error, lastUpdated, analyze }), [response, source, loading, error, lastUpdated, demoMode]);
  return <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>;
}

export function useAnalysis() {
  const value = useContext(AnalysisContext);
  if (!value) throw new Error("useAnalysis must be used within AnalysisProvider");
  return value;
}
