import { ChangeEvent, DragEvent, useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, CloudUpload, FileImage, Image as ImageIcon, Mountain, RefreshCw, ShieldAlert, Sparkles, Trash2 } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { convertLandslideImage, predictLandslide, type LandslidePredictionResponse } from "@/services/landslideApi";

const allowedTypes = ["image/jpeg", "image/png", "image/tiff"];
const allowedExtensions = ["jpg", "jpeg", "png", "tif", "tiff"];

function formatSize(bytes: number) {
  return bytes < 1024 * 1024 ? `${Math.round(bytes / 1024)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function assetUrl(value?: string) {
  if (!value) return undefined;
  if (value.startsWith("http") || value.startsWith("blob:") || value.startsWith("data:") || value.startsWith("/")) return value;
  return `${import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"}/${value}`;
}

export default function LandslideDetection() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>();
  const [result, setResult] = useState<LandslidePredictionResponse | null>(null);
  const [view, setView] = useState<"original" | "mask" | "overlay">("original");
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => () => { if (previewUrl && previewUrl.startsWith("blob:")) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const origSrc = useMemo(() => assetUrl(result?.original_image || result?.original_url) || previewUrl, [result, previewUrl]);
  const maskSrc = useMemo(() => assetUrl(result?.mask_image || result?.mask_url), [result]);
  const overlaySrc = useMemo(() => assetUrl(result?.overlay_image || result?.overlay_url), [result]);

  const displayImage = useMemo(
    () => (view === "original" ? origSrc : view === "mask" ? maskSrc : overlaySrc),
    [view, origSrc, maskSrc, overlaySrc]
  );

  async function chooseFile(candidate?: File) {
    if (!candidate) return;
    const extension = candidate.name.split(".").pop()?.toLowerCase() || "";
    if (!allowedTypes.includes(candidate.type) && !allowedExtensions.includes(extension)) {
      setError("Please choose a JPG, JPEG, PNG, or TIFF terrain image.");
      return;
    }
    if (candidate.size > 15 * 1024 * 1024) {
      setError("Please choose an image smaller than 15 MB.");
      return;
    }
    if (previewUrl && previewUrl.startsWith("blob:")) URL.revokeObjectURL(previewUrl);
    setFile(candidate);
    setResult(null);
    setError("");
    setView("original");

    // If TIFF file or image, attempt backend conversion to Base64 PNG for instant browser preview
    if (extension === "tif" || extension === "tiff" || candidate.type.includes("tiff")) {
      try {
        const converted = await convertLandslideImage(candidate);
        setPreviewUrl(converted.image_data);
        return;
      } catch (err) {
        console.warn("Failed to convert TIFF preview via backend, using Blob fallback", err);
      }
    }
    setPreviewUrl(URL.createObjectURL(candidate));
  }

  function onInput(event: ChangeEvent<HTMLInputElement>) {
    chooseFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files?.[0]);
  }

  function removeFile() {
    if (previewUrl && previewUrl.startsWith("blob:")) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(undefined);
    setResult(null);
    setError("");
    setView("original");
  }

  async function analyze() {
    if (!file) {
      setError("Upload a terrain image before starting analysis.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await predictLandslide(file);
      setResult(response);
      if (response.original_image || response.original_url) {
        const serverOrig = assetUrl(response.original_image || response.original_url);
        if (serverOrig) setPreviewUrl(serverOrig);
      }
      setView(response.overlay_image || response.overlay_url ? "overlay" : response.mask_image || response.mask_url ? "mask" : "original");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to analyze this image. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const statusText = result?.prediction || result?.result || "Response received";
  const isDetected = statusText.toUpperCase().includes("DETECTED") && !statusText.toUpperCase().includes("NO SIGNIFICANT");
  const hasRegions = result?.detected_regions && result.detected_regions.length > 0;

  return (
    <AppShell eyebrow="Environmental intelligence / image analysis" title="Landslide Detection">
      <div className="space-y-6">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <div className="flex items-center gap-3">
              <div className="grid size-10 place-items-center rounded-xl bg-[#e5f8fb] text-[#0b9db7]">
                <Mountain size={20} />
              </div>
              <div>
                <h2 className="text-xl font-semibold tracking-[-0.03em] text-[#0a1858]">Terrain image analysis</h2>
                <p className="mt-1 text-sm text-[#73869f]">Upload a terrain image to detect potential landslide-prone regions using DeepLabV3 AI model.</p>
              </div>
            </div>
          </div>
          <span className={`inline-flex items-center gap-2 self-start rounded-full border px-2.5 py-1.5 text-[10px] font-mono uppercase tracking-[0.12em] sm:self-auto ${loading ? "border-[#f2dfb2] bg-[#fffaf0] text-[#80601c]" : result ? "border-[#bdebdc] bg-[#effcf6] text-[#187957]" : "border-[#bfe6ef] bg-[#eafbfd] text-[#28667d]"}`}>
            <span className={`size-1.5 rounded-full ${loading ? "animate-pulse bg-[#f5b942]" : result ? "bg-[#35d6a1]" : "bg-[#19c8e8]"}`} />
            {loading ? "LOADING" : result ? "API RESPONSE" : "IMAGE MODEL / READY"}
          </span>
        </div>

        <div className="grid gap-6 xl:grid-cols-[.8fr_1.2fr]">
          <section className="space-y-4">
            <div
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              className={`relative rounded-2xl border-2 border-dashed p-6 transition ${dragging ? "border-[#19c8e8] bg-[#eafbfd]" : "border-[#c5dfe9] bg-white"}`}
            >
              <input ref={inputRef} type="file" accept=".jpg,.jpeg,.png,.tif,.tiff,image/*" className="sr-only" onChange={onInput} />
              <div className="flex min-h-[270px] flex-col items-center justify-center text-center">
                <div className="grid size-14 place-items-center rounded-2xl bg-[#e5f8fb] text-[#0b9db7] shadow-sm">
                  <CloudUpload size={26} />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-[#102052]">Upload Terrain Image</h3>
                <p className="mt-2 text-sm text-[#73869f]">
                  Drag and drop an image here or <button type="button" onClick={() => inputRef.current?.click()} className="font-semibold text-[#3979f6] hover:underline">browse files</button>
                </p>
                <p className="mt-3 text-[10px] font-mono uppercase tracking-[0.14em] text-[#9aabba]">JPG · JPEG · PNG · TIFF · max 15 MB</p>
              </div>
            </div>

            {file && (
              <div className="flex items-center gap-3 rounded-xl border border-[#d7e8f1] bg-white p-3">
                <div className="grid size-10 place-items-center rounded-lg bg-[#f1f6f9] text-[#3979f6]">
                  <FileImage size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium text-[#102052]">{file.name}</div>
                  <div className="mt-1 text-[11px] text-[#73869f]">{formatSize(file.size)} · ready for analysis</div>
                </div>
                <button type="button" onClick={removeFile} className="grid size-8 place-items-center rounded-lg text-[#73869f] hover:bg-[#fff5f6] hover:text-[#c94359]" aria-label="Remove image">
                  <Trash2 size={15} />
                </button>
                <button type="button" onClick={() => inputRef.current?.click()} className="rounded-lg border border-[#d7e8f1] px-3 py-2 text-[10px] font-mono uppercase tracking-[0.1em] text-[#3979f6] hover:bg-[#f6fbfd]">Replace</button>
              </div>
            )}

            {error && (
              <div className="flex items-start gap-2 rounded-xl border border-[#f4c6cd] bg-[#fff5f6] p-3 text-xs leading-relaxed text-[#a94455]">
                <AlertTriangle size={15} className="mt-0.5 shrink-0" />
                {error}
              </div>
            )}

            <button type="button" onClick={analyze} disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#080d4d] px-5 py-3.5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-[#101a70] disabled:cursor-wait disabled:opacity-70">
              {loading ? <><RefreshCw size={17} className="animate-spin" /> Analyzing terrain patterns…</> : <><Sparkles size={17} /> Analyze for Landslides</>}
            </button>

            <div className="flex items-start gap-2 rounded-xl border border-[#f2dfb2] bg-[#fffaf0] p-3 text-[11px] leading-relaxed text-[#80601c]">
              <ShieldAlert size={14} className="mt-0.5 shrink-0" />
              Experimental DeepLabV3-ResNet50 image segmentation model output. Not a live disaster warning.
            </div>
          </section>

          <section className="rounded-2xl border border-[#d7e8f1] bg-white p-5 shadow-[0_10px_30px_rgba(11,46,83,0.04)] sm:p-6">
            <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
              <div>
                <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-[#3979f6]">Segmentation workspace</div>
                <h2 className="mt-2 text-lg font-semibold text-[#102052]">Terrain visualization</h2>
              </div>
              <div className="flex w-full justify-between rounded-lg border border-[#d7e8f1] bg-[#f8fbfd] p-1 sm:w-auto">
                {(["original", "mask", "overlay"] as const).map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setView(item)}
                    className={`flex-1 rounded-md px-2.5 py-1.5 text-[10px] font-mono uppercase tracking-[0.08em] sm:flex-none ${view === item ? "bg-[#080d4d] text-white" : "text-[#73869f]"}`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-5 flex min-h-[340px] items-center justify-center overflow-hidden rounded-xl border border-[#d7e8f1] bg-[#edf5f8]">
              {displayImage ? (
                <img
                  src={displayImage}
                  alt={view === "original" ? "Uploaded terrain" : `${view} returned by landslide model`}
                  className="max-h-[420px] w-full object-contain"
                />
              ) : (
                <div className="max-w-xs text-center">
                  <ImageIcon className="mx-auto text-[#9bb4c3]" size={34} />
                  <p className="mt-3 text-sm font-medium text-[#526d84]">
                    {view === "original" ? "Your terrain preview will appear here." : `No ${view} image returned by backend.`}
                  </p>
                  <p className="mt-2 text-xs leading-5 text-[#8195a6]">Upload a terrain image and click Analyze to generate mask and overlay.</p>
                </div>
              )}
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3 text-[10px] font-mono uppercase tracking-[0.1em] text-[#73869f]">
              <span className="flex items-center gap-1.5"><span className="size-2 rounded-full bg-[#e85b6b]" /> highlighted region from PyTorch model</span>
              <span className="text-[#a4b4c0]">·</span>
              <span>DeepLabV3-ResNet50 (2 classes)</span>
            </div>
          </section>
        </div>

        {result ? (
          <section className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div className={`rounded-2xl border p-5 ${isDetected ? "border-[#f2c6cd] bg-[#fff5f6]" : "border-[#bdebdc] bg-[#effcf6]"}`}>
                <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-[#73869f]">Prediction status</div>
                <div className="mt-3 flex items-center gap-2 text-sm font-semibold text-[#102052]">
                  {isDetected ? <AlertTriangle size={17} className="text-[#d74960]" /> : <CheckCircle2 size={17} className="text-[#187957]" />}
                  {statusText}
                </div>
              </div>

              <div className="rounded-2xl border border-[#d7e8f1] bg-white p-5">
                <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-[#73869f]">Risk level</div>
                <div className="mt-3 text-2xl font-semibold text-[#0a1858]">{result.risk_level || "Not provided"}</div>
              </div>

              <div className="rounded-2xl border border-[#d7e8f1] bg-white p-5">
                <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-[#73869f]">Landslide coverage</div>
                <div className="mt-3 text-2xl font-semibold text-[#0a1858]">
                  {result.landslide_percentage !== undefined ? `${result.landslide_percentage}%` : "Not provided"}
                </div>
              </div>

              <div className="rounded-2xl border border-[#d7e8f1] bg-white p-5">
                <div className="text-[10px] font-mono uppercase tracking-[0.14em] text-[#73869f]">Model confidence</div>
                <div className="mt-3 text-2xl font-semibold text-[#0a1858]">
                  {typeof result.confidence === "number" ? `${Math.round(result.confidence)}%` : "Not provided"}
                </div>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.1fr_.9fr]">
              <section className="rounded-2xl border border-[#d7e8f1] bg-white p-5 shadow-[0_10px_30px_rgba(11,46,83,0.04)]">
                <h2 className="text-lg font-semibold text-[#102052]">Segmentation Details</h2>
                <p className="mt-2 text-sm leading-6 text-[#73869f]">DeepLabV3-ResNet50 inference metrics and pixel breakdown.</p>
                <div className="mt-5 space-y-3">
                  <div className="rounded-xl border border-[#d7e8f1] bg-[#f8fbfd] p-4 text-xs text-[#294366]">
                    <div className="flex justify-between border-b border-[#e6eff4] pb-2 font-mono">
                      <span>Original Image Dimensions:</span>
                      <span className="font-semibold text-[#0a1858]">{result.original_image_size ? `${result.original_image_size.width} × ${result.original_image_size.height}` : "N/A"}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#e6eff4] py-2 font-mono">
                      <span>Prediction Mask Dimensions:</span>
                      <span className="font-semibold text-[#0a1858]">{result.mask_dimensions ? `${result.mask_dimensions.width} × ${result.mask_dimensions.height}` : "N/A"}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#e6eff4] py-2 font-mono">
                      <span>Landslide Pixels:</span>
                      <span className="font-semibold text-[#0a1858]">{result.predicted_landslide_pixels?.toLocaleString() ?? "N/A"} / {result.total_pixels?.toLocaleString() ?? "N/A"}</span>
                    </div>
                    <div className="flex justify-between pt-2 font-mono">
                      <span>Coverage Ratio:</span>
                      <span className="font-semibold text-[#0a1858]">{result.landslide_percentage}%</span>
                    </div>
                  </div>
                </div>
              </section>

              <section className="rounded-2xl border border-[#d7e8f1] bg-[#0b1859] p-5 text-white shadow-[0_16px_38px_rgba(11,46,83,0.12)]">
                <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-cyan-200">Model interpretation</div>
                <p className="mt-4 text-sm leading-7 text-slate-300">
                  {result.explanation || "This response reflects genuine DeepLabV3-ResNet50 PyTorch model inference."}
                </p>
                <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.05] p-4 text-xs leading-6 text-slate-400">
                  {result.disclaimer || "AI-based image segmentation output derived from trained PyTorch model. Not intended as a certified live disaster forecast."}
                </div>
              </section>
            </div>
          </section>
        ) : (
          <section className="rounded-2xl border border-dashed border-[#c5dfe9] bg-[#f8fbfd] p-6 text-center">
            <div className="mx-auto grid size-11 place-items-center rounded-full bg-[#e5f8fb] text-[#0b9db7]">
              <ImageIcon size={19} />
            </div>
            <h3 className="mt-4 font-semibold text-[#102052]">No prediction yet</h3>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#73869f]">
              Upload a terrain image (JPG, PNG, TIFF), then click “Analyze for Landslides” to perform PyTorch segmentation inference.
            </p>
          </section>
        )}
      </div>
    </AppShell>
  );
}
