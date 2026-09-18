export interface DetectedRegion { id?: string | number; area?: number; area_percentage?: number; bbox?: number[]; coordinates?: number[][]; risk_level?: string; label?: string; }
export interface LandslidePredictionResponse { prediction?: string; risk_level?: "Low" | "Medium" | "High" | string; confidence?: number; processing_time?: number; processing_time_ms?: number; mask_url?: string; overlay_url?: string; detected_regions?: DetectedRegion[]; disclaimer?: string; explanation?: string; }

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8003";
const PREDICT_URL = import.meta.env.VITE_LANDSLIDE_PREDICTION_URL || `${API_BASE_URL}/predict-landslide`;

export class LandslideApiError extends Error { constructor(message: string) { super(message); this.name = "LandslideApiError"; } }

export async function predictLandslide(file: File): Promise<LandslidePredictionResponse> {
  const body = new FormData();
  body.append("file", file);
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(PREDICT_URL, { method: "POST", body, signal: controller.signal });
    if (!response.ok) throw new LandslideApiError(response.status >= 500 ? "The landslide analysis service returned a server error." : "The uploaded image was rejected by the analysis service.");
    const payload = await response.json().catch(() => null);
    if (!payload || typeof payload !== "object") throw new LandslideApiError("The analysis service returned an invalid prediction response.");
    return payload as LandslidePredictionResponse;
  } catch (error) {
    if (error instanceof LandslideApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") throw new LandslideApiError("Analysis timed out. Check that the FastAPI server is running and try again.");
    throw new LandslideApiError("Unable to reach the landslide analysis service. Check that the FastAPI server is running.");
  } finally { window.clearTimeout(timeout); }
}
