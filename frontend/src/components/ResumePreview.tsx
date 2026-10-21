"use client";

import { useState } from "react";
import { exportPdfBlob } from "@/lib/api";

interface ResumePreviewProps {
  pdfBase64?: string | null;
  htmlContent?: string | null;
  resumeData?: any;
  talkingPoints?: string[];
}

export function ResumePreview({
  pdfBase64,
  htmlContent,
  resumeData,
  talkingPoints = [],
}: ResumePreviewProps) {
  const [activeTab, setActiveTab] = useState<"pdf" | "html" | "prep">("pdf");
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    if (!resumeData && !pdfBase64) return;
    try {
      setDownloading(true);
      let blob: Blob;

      if (resumeData) {
        blob = await exportPdfBlob(resumeData);
      } else if (pdfBase64) {
        const byteCharacters = atob(pdfBase64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        blob = new Blob([byteArray], { type: "application/pdf" });
      } else {
        return;
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "Gunnam_Sai_Saketh_Ram_Resume.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download failed:", err);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex flex-col h-full rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm overflow-hidden min-h-[650px]">
      {/* Top Header & Tab Controls */}
      <div className="flex flex-wrap items-center justify-between p-4 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50">
        <div className="flex items-center gap-1 bg-zinc-200/60 dark:bg-zinc-800/60 p-1 rounded-xl">
          <button
            type="button"
            onClick={() => setActiveTab("pdf")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "pdf"
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-xs"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
            }`}
          >
            📄 PDF Page (1-Page Fit)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("html")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "html"
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-xs"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
            }`}
          >
            🌐 Web View
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("prep")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "prep"
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-xs"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
            }`}
          >
            🎙️ Interview Prep ({talkingPoints.length})
          </button>
        </div>

        {(pdfBase64 || resumeData) && (
          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            className="px-3.5 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs disabled:opacity-50"
          >
            {downloading ? "Preparing..." : "⬇ Download 1-Page PDF"}
          </button>
        )}
      </div>

      {/* Main View Area */}
      <div className="flex-1 bg-zinc-100/50 dark:bg-zinc-950/50 p-4 flex flex-col justify-center">
        {activeTab === "pdf" && (
          <div className="w-full h-full min-h-[600px] flex items-center justify-center">
            {pdfBase64 ? (
              <iframe
                src={`data:application/pdf;base64,${pdfBase64}#toolbar=0&navpanes=0&scrollbar=0`}
                className="w-full h-full min-h-[640px] rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-md bg-white"
                title="Generated PDF Resume"
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-center p-8 max-w-sm mx-auto">
                <div className="w-14 h-14 rounded-2xl bg-zinc-200/50 dark:bg-zinc-800/50 flex items-center justify-center text-2xl mb-3">
                  📑
                </div>
                <h4 className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
                  No Resume Generated Yet
                </h4>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                  Paste a job description on the left to synthesize Saketh's tailored, strictly 1-page PDF resume.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "html" && (
          <div className="w-full h-full min-h-[600px] flex items-center justify-center">
            {htmlContent ? (
              <iframe
                srcDoc={htmlContent}
                className="w-full h-full min-h-[640px] rounded-xl border border-zinc-200 dark:border-zinc-800 shadow-md bg-white"
                title="HTML Resume Preview"
              />
            ) : (
              <div className="text-xs text-zinc-500 text-center">
                Web preview will render when a resume is generated.
              </div>
            )}
          </div>
        )}

        {activeTab === "prep" && (
          <div className="w-full h-full min-h-[500px] p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 overflow-y-auto">
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-3">
              Strategic Interview Talking Points
            </h3>
            {talkingPoints.length > 0 ? (
              <div className="space-y-3">
                {talkingPoints.map((pt, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-xl border border-blue-100 dark:border-blue-900/30 bg-blue-50/30 dark:bg-blue-950/20 text-xs text-zinc-800 dark:text-zinc-200 leading-relaxed"
                  >
                    <span className="font-bold text-blue-600 dark:text-blue-400 mr-2">
                      #{i + 1}
                    </span>
                    {pt}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-500">
                Generate a resume to extract personalized interview defense arguments based on this role.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
