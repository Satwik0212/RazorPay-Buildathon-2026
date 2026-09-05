import React, { useCallback, useRef, useState } from "react";
import { Upload, CheckCircle, AlertTriangle, ArrowRight, X, Loader2, FileText, Zap, Brain } from "lucide-react";
import { Button } from "../../ui/Button";
import { ReviewResolveStage } from "./ReviewResolveStage";
import { catalogueImportApi } from "../../../api/catalogueImport";
import type { ImportPreviewResponse, ImportResultResponse } from "../../../api/catalogueImport";

type Step = "upload" | "mapping" | "resolve" | "preview" | "success";

interface Props {
  onClose: () => void;
  onImportComplete: () => void;
}

const CONFIDENCE_COLOR = {
  HIGH: "text-green-600 bg-green-50",
  MEDIUM: "text-yellow-600 bg-yellow-50",
  LOW: "text-red-600 bg-red-50",
};

export const ImportCatalogueModal: React.FC<Props> = ({ onClose, onImportComplete }) => {
  const [step, setStep] = useState<Step>("upload");
  const [dragging, setDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploadPercent, setUploadPercent] = useState<number | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [result, setResult] = useState<ImportResultResponse | null>(null);
  const [error, setError] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Only CSV files are accepted.");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError("File too large. Maximum size is 50MB.");
      return;
    }
    setSelectedFile(file);
    setError("");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setAnalyzing(true);
    setUploadPercent(0);
    setError("");
    try {
      const resp = await catalogueImportApi.analyze(selectedFile, (percent) => {
        setUploadPercent(percent);
      });
      setPreview(resp.data);
      setStep("mapping");
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Failed to analyze file. Please try again.";
      setError(msg);
    } finally {
      setAnalyzing(false);
      setUploadPercent(null);
    }
  };

  const handleConfirm = async () => {
    if (!preview) return;
    setConfirming(true);
    setError("");
    try {
      const resp = await catalogueImportApi.confirm(preview.import_job_id);
      setResult(resp.data);
      setStep("success");
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Import failed. Please try again.";
      setError(msg);
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">AI Catalogue Import</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Step Indicator */}
        <div className="flex items-center justify-between px-6 py-3 bg-gray-50 border-b border-gray-100 text-xs font-medium">
          {["Upload", "Review Mapping", "Preview Import", "Done"].map((label, i) => {
            const stepKeys: Step[] = ["upload", "mapping", "preview", "success"];
            const isActive = stepKeys[i] === step;
            const isDone = ["upload", "mapping", "preview", "success"].indexOf(step) > i;
            return (
              <div key={label} className="flex items-center gap-1">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                  isDone ? "bg-green-500 text-white" : isActive ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-500"
                }`}>
                  {isDone ? "✓" : i + 1}
                </span>
                <span className={isActive ? "text-blue-700 font-semibold" : isDone ? "text-green-600" : "text-gray-400"}>
                  {label}
                </span>
                {i < 3 && <ArrowRight className="w-3 h-3 text-gray-300 mx-1" />}
              </div>
            );
          })}
        </div>

        <div className="p-6">
          {/* STEP 1: Upload */}
          {step === "upload" && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-gray-800 mb-1">Upload Your Product Catalogue</h3>
                <p className="text-sm text-gray-500">
                  Upload a CSV file. GraahakLens will intelligently detect your columns, map them to the canonical
                  product schema, and preview results before any data is written.
                </p>
              </div>

              {/* Drop Zone */}
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
                  dragging ? "border-blue-400 bg-blue-50" : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/30"
                }`}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
                />
                <Upload className="w-10 h-10 mx-auto text-blue-400 mb-3" />
                {selectedFile ? (
                  <div>
                    <p className="text-sm font-semibold text-blue-700">{selectedFile.name}</p>
                    <p className="text-xs text-gray-500 mt-1">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-gray-700">Drop your CSV here or <span className="text-blue-600 underline">browse</span></p>
                    <p className="text-xs text-gray-400 mt-1">CSV only · Max 50MB · Max 10,000 rows</p>
                  </div>
                )}
              </div>

              {/* Supported note */}
              <div className="flex items-start gap-2 bg-blue-50 rounded-lg px-4 py-3 text-xs text-blue-700">
                <Zap className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Flipkart CSV</strong> format is recognized instantly without AI.
                  Other formats use AI schema mapping with your explicit review.
                </span>
              </div>

              {analyzing && uploadPercent !== null && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-gray-500 font-medium">
                    <span>{uploadPercent < 100 ? `Uploading ${(selectedFile?.size ? (selectedFile.size / (1024 * 1024)).toFixed(1) : '')} MB...` : "Processing & analyzing schema..."}</span>
                    <span>{uploadPercent}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-150"
                      style={{ width: `${uploadPercent}%` }}
                    />
                  </div>
                </div>
              )}

              {error && <p className="text-sm text-red-600">{error}</p>}

              <Button
                onClick={handleAnalyze}
                disabled={!selectedFile || analyzing}
                className="w-full"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {uploadPercent !== null && uploadPercent < 100
                      ? `Uploading (${uploadPercent}%)...`
                      : "Analyzing schema & validating rows..."}
                  </>
                ) : (
                  <><Brain className="w-4 h-4 mr-2" /> Analyze CSV</>
                )}
              </Button>
            </div>
          )}

          {/* STEP 2: Mapping Review */}
          {step === "mapping" && preview && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold text-gray-800">Schema Mapping Review</h3>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  preview.schema_type === "FLIPKART_CANONICAL" ? "bg-green-100 text-green-700" :
                  preview.ai_mapper_used ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"
                }`}>
                  {preview.schema_type === "FLIPKART_CANONICAL" ? "⚡ Flipkart Fast-Path" :
                   preview.ai_mapper_used ? "🧠 AI Mapped" : "🔗 Alias Mapped"}
                </span>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: "Total Rows", value: preview.total_rows, color: "text-gray-700" },
                  { label: "Ready", value: preview.ready_row_count, color: "text-green-700" },
                  { label: "Needs Review", value: preview.needs_review_row_count, color: "text-amber-600" },
                  { label: "Needs Fix", value: preview.needs_fix_row_count + preview.duplicate_row_count, color: "text-red-600" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className={`text-lg font-bold ${color}`}>{value.toLocaleString()}</p>
                    <p className="text-[10px] text-gray-500 uppercase mt-0.5">{label}</p>
                  </div>
                ))}
              </div>

              {/* Mappings table */}
              <div className="rounded-lg border border-gray-100 overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Your CSV Column</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">→ Canonical Field</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-600">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {preview.mappings.map((m) => (
                      <tr key={m.source_column} className="hover:bg-gray-50">
                        <td className="px-3 py-2 font-mono text-gray-700">{m.source_column}</td>
                        <td className="px-3 py-2 text-blue-700 font-medium">{m.target_field}</td>
                        <td className="px-3 py-2">
                          <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${CONFIDENCE_COLOR[m.confidence_level]}`}>
                            {Math.round(m.confidence * 100)}% {m.confidence_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {preview.unmapped_source_columns.length > 0 && (
                <div className="text-xs text-gray-500">
                  <strong>Unmapped columns (will be skipped):</strong>{" "}
                  {preview.unmapped_source_columns.join(", ")}
                </div>
              )}

              {preview.has_low_confidence_mappings && (
                <div className="flex items-center gap-2 bg-yellow-50 rounded-lg px-3 py-2 text-xs text-yellow-700">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  Some mappings have LOW confidence. Review carefully before confirming.
                </div>
              )}

              {preview.warnings.length > 0 && (
                <div className="text-xs text-amber-700 space-y-1">
                  {preview.warnings.map((w, i) => <p key={i}>⚠ {w}</p>)}
                </div>
              )}

              {error && <p className="text-sm text-red-600">{error}</p>}

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep("upload")} className="flex-1">← Back</Button>
                <Button
                  onClick={() => {
                        if (preview.needs_fix_row_count > 0 || preview.needs_review_row_count > 0) {
                          setStep("resolve");
                        } else {
                          setStep("preview");
                        }
                      }}
                  disabled={preview.ready_row_count === 0 && preview.needs_fix_row_count === 0 && preview.needs_review_row_count === 0}
                  className="flex-1"
                >
                  Preview Import ({preview.ready_row_count} products) →
                </Button>
              </div>
            </div>
          )}

          
          {/* STEP 2.5: Resolve */}
          {step === "resolve" && preview && (
            <ReviewResolveStage 
              importJobId={preview.import_job_id} 
              onResolvedAll={() => {
                setStep("preview");
                // update local preview object? we might need to refetch analysis.
                // for now, we just proceed.
              }} 
              onCancel={() => setStep("mapping")} 
            />
          )}

          {/* STEP 3: Preview */}
          {step === "preview" && preview && (
            <div className="space-y-4">
              <h3 className="text-base font-semibold text-gray-800">Import Preview</h3>

              {preview.sample_normalized.slice(0, 3).map((row: any, i) => (
                <div key={i} className="bg-gray-50 rounded-lg p-3 text-xs space-y-1">
                  <p className="font-semibold text-gray-800 truncate">{row.product_name}</p>
                  <div className="flex gap-3 text-gray-500">
                    <span>Category: <strong className="text-gray-700">{row.category || "—"}</strong></span>
                    {row.discounted_price && <span>Price: <strong className="text-gray-700">₹{(row.discounted_price / 100).toFixed(2)}</strong></span>}
                    {row.brand && <span>Brand: <strong className="text-gray-700">{row.brand}</strong></span>}
                  </div>
                </div>
              ))}

              <div className="bg-blue-50 rounded-lg px-4 py-3 text-sm text-blue-800">
                <strong>{preview.ready_row_count} products</strong> will be added to your catalogue.
                {preview.excluded_row_count > 0 && (
                  <span className="text-amber-700 ml-1">{preview.excluded_row_count} rows were manually excluded.</span>
                )}
              </div>

              <p className="text-xs text-gray-500">
                Existing products with the same name will be skipped. No existing data will be overwritten.
              </p>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep("mapping")} className="flex-1">← Back</Button>
                <Button onClick={handleConfirm} disabled={confirming} className="flex-1">
                  {confirming ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Importing…</>
                  ) : (
                    <>Confirm Import ({preview.ready_row_count} products)</>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* STEP 4: Success */}
          {step === "success" && result && (
            <div className="text-center space-y-4 py-4">
              <CheckCircle className="w-14 h-14 text-green-500 mx-auto" />
              <h3 className="text-lg font-bold text-gray-900">Import Complete</h3>

              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Products Added", value: result.inserted, color: "text-green-700" },
                  { label: "Already Existed", value: result.skipped_existing, color: "text-gray-600" },
                  { label: "Failed", value: result.failed, color: result.failed > 0 ? "text-red-600" : "text-gray-400" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className={`text-xl font-bold ${color}`}>{value}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{label}</p>
                  </div>
                ))}
              </div>

              {result.inserted > 0 && (
                <p className="text-sm text-gray-600">
                  {result.inserted} products have been added to your catalogue and are ready for AI buyer simulation.
                </p>
              )}

              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={onClose} className="flex-1">Close</Button>
                <Button onClick={() => { onImportComplete(); onClose(); }} className="flex-1">
                  <FileText className="w-4 h-4 mr-2" /> View Catalogue
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
