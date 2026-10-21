"use client";

import { useState } from "react";
import { exportPdfBlob, ImprovementPlaybook } from "@/lib/api";

interface ResumePreviewProps {
  pdfBase64?: string | null;
  htmlContent?: string | null;
  resumeData?: any;
  talkingPoints?: string[];
  playbook?: ImprovementPlaybook | null;
}

export function ResumePreview({
  pdfBase64,
  htmlContent,
  resumeData,
  talkingPoints = [],
  playbook,
}: ResumePreviewProps) {
  const [activeTab, setActiveTab] = useState<"pdf" | "html" | "playbook" | "prep">("pdf");
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
      a.download = "Tailored_Resume.pdf";
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
            📄 PDF (1-Page)
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
            onClick={() => setActiveTab("playbook")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === "playbook"
                ? "bg-white dark:bg-zinc-700 text-blue-600 dark:text-blue-400 shadow-xs font-bold"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
            }`}
          >
            📅 30-Day Sprint Plan
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
                  Ready to Synthesize
                </h4>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
                  Upload a resume or use the master profile, paste a job description, and click generate to synthesize your tailored 1-page PDF.
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

        {activeTab === "playbook" && (
          <div className="w-full h-full min-h-[500px] p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 overflow-y-auto space-y-4">
            {playbook ? (
              <>
                <div className="flex items-center justify-between border-b border-zinc-200 dark:border-zinc-800 pb-3">
                  <div>
                    <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide">
                      30-Day Sprint to 90%+ Interview Readiness
                    </h3>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">
                      Target: <b>{playbook.target_role}</b> at <b>{playbook.target_company}</b>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2.5 py-1 rounded-lg bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-bold border border-blue-200 dark:border-blue-800">
                      Current: {playbook.current_match_percentage}%
                    </span>
                    <span className="text-xs text-zinc-400">➔</span>
                    <span className="text-xs px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-800">
                      Projected: {playbook.projected_match_percentage}%
                    </span>
                  </div>
                </div>

                <p className="text-xs text-zinc-600 dark:text-zinc-300 bg-zinc-50 dark:bg-zinc-950 p-3 rounded-xl border border-zinc-200 dark:border-zinc-800 leading-relaxed">
                  💡 {playbook.advisor_summary}
                </p>

                <div className="space-y-3">
                  {playbook.sprint_weeks.map((week) => (
                    <div
                      key={week.week_number}
                      className="p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-950/40 text-xs space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-blue-600 dark:text-blue-400">
                          WEEK {week.week_number} — {week.title}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 font-mono">
                          {week.deliverable}
                        </span>
                      </div>
                      <p className="text-zinc-500 dark:text-zinc-400 text-[11px] italic">
                        {week.focus}
                      </p>
                      <ul className="space-y-1 text-zinc-700 dark:text-zinc-300 text-[11px]">
                        {week.action_items.map((action, aIdx) => (
                          <li key={aIdx} className="flex items-start gap-1.5">
                            <span className="text-emerald-500 font-bold">✓</span>
                            <span>{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-xs text-zinc-500 text-center py-12">
                Generate a resume to calculate your 30-day candidate readiness sprint plan.
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
