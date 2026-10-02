"use client";

import { useEffect, useState } from "react";
import { getDeepHealth, DeepHealthResponse } from "@/lib/api";
import { JDInput } from "@/components/JDInput";
import { ResumePreview } from "@/components/ResumePreview";
import { InterviewScore } from "@/components/InterviewScore";
import { ChangeLog } from "@/components/ChangeLog";

export default function Home() {
  const [health, setHealth] = useState<DeepHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDeepHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to reach backend");
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col font-sans">
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm sticky top-0 z-10 px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            ResumePilot AI
          </h1>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Deterministic AI Resume Intelligence & Tailoring Engine
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono border border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-900">
            <span
              className={`w-2 h-2 rounded-full ${
                loading
                  ? "bg-amber-400 animate-pulse"
                  : health?.status === "ok"
                  ? "bg-emerald-500"
                  : "bg-rose-500"
              }`}
            />
            <span>
              {loading
                ? "Connecting..."
                : health?.status === "ok"
                ? `Connected · dim=${health.embedding_dim} · Groq=${health.groq_reply}`
                : `Error: ${error || "Unreachable"}`}
            </span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 flex flex-col gap-6">
          <JDInput />
          <InterviewScore />
          <ChangeLog />
        </div>

        <div className="lg:col-span-6 flex flex-col">
          <ResumePreview />
        </div>
      </main>

      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-4 px-6 text-center text-xs text-zinc-400">
        ResumePilot AI · Single-User Optimized · Zero Hallucination Truth Engine
      </footer>
    </div>
  );
}
