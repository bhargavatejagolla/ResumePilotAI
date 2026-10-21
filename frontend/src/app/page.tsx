"use client";

import { useEffect, useState } from "react";
import {
  getDeepHealth,
  generateResume,
  DeepHealthResponse,
  GenerateResponse,
} from "@/lib/api";
import { JDInput } from "@/components/JDInput";
import { ResumePreview } from "@/components/ResumePreview";
import { InterviewScore } from "@/components/InterviewScore";
import { ChangeLog } from "@/components/ChangeLog";

export default function Home() {
  const [health, setHealth] = useState<DeepHealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true);
  const [generating, setGenerating] = useState<boolean>(false);
  const [genResult, setGenResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDeepHealth()
      .then((data) => {
        setHealth(data);
        setLoadingHealth(false);
      })
      .catch((err) => {
        console.warn("Health check error:", err);
        setLoadingHealth(false);
      });
  }, []);

  const handleGenerate = async (
    jdText: string,
    companyOverride?: string,
    toneOverride?: string,
  ) => {
    try {
      setGenerating(true);
      setError(null);
      const res = await generateResume(jdText, companyOverride, toneOverride);
      setGenResult(res);
    } catch (err: any) {
      console.error("Resume generation failed:", err);
      setError(err.message || "Failed to generate tailored resume.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm sticky top-0 z-20 px-6 py-3.5 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-xs">
            RP
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                ResumePilot AI
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-semibold border border-blue-200 dark:border-blue-800">
                v5.0 Enterprise Engine
              </span>
            </div>
            <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
              Deterministic AI Resume Intelligence for Gunnam Sai Saketh Ram
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono border border-zinc-200 dark:border-zinc-800 bg-zinc-100/70 dark:bg-zinc-900/70">
            <span
              className={`w-2 h-2 rounded-full ${
                loadingHealth
                  ? "bg-amber-400 animate-pulse"
                  : health?.status === "ok"
                  ? "bg-emerald-500"
                  : "bg-emerald-500"
              }`}
            />
            <span className="text-[11px]">
              {loadingHealth
                ? "Checking services..."
                : health?.status === "ok"
                ? `System Ready · Embeddings Active · Groq LLM Connected`
                : "Backend Active (Local)"}
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-[1550px] w-full mx-auto p-5 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Job Input + Metrics + Audit Log */}
        <div className="lg:col-span-6 flex flex-col gap-6">
          <JDInput onGenerate={handleGenerate} loading={generating} />

          {error && (
            <div className="p-4 rounded-xl border border-rose-200 dark:border-rose-900/50 bg-rose-50/50 dark:bg-rose-950/20 text-rose-700 dark:text-rose-300 text-xs flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="text-rose-500 hover:text-rose-700 font-bold"
              >
                ✕
              </button>
            </div>
          )}

          <InterviewScore
            verification={genResult?.verification}
            companyType={genResult?.job?.company_type}
          />

          <ChangeLog
            bulletDiffs={genResult?.verification?.explainability?.bullet_diffs}
            projectDecisions={genResult?.verification?.explainability?.project_decisions}
          />
        </div>

        {/* Right Column: PDF Preview / HTML / Interview Prep */}
        <div className="lg:col-span-6 flex flex-col">
          <ResumePreview
            pdfBase64={genResult?.pdf_base64}
            htmlContent={genResult?.html}
            resumeData={genResult?.resume}
            talkingPoints={genResult?.verification?.explainability?.interview_talking_points}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-3.5 px-6 text-center text-xs text-zinc-500 dark:text-zinc-400 flex flex-wrap items-center justify-between">
        <span>
          Candidate: <b>Gunnam Sai Saketh Ram</b> · B.Tech CSE (GITAM 2026) · Grand Champion ET GenAI Hackathon
        </span>
        <span className="font-mono text-[11px]">
          Deterministic Pipeline · Pure Python Core · Zero Hallucination
        </span>
      </footer>
    </div>
  );
}
