"use client";

import { useState } from "react";

interface JDInputProps {
  onGenerate: (jdText: string, companyOverride?: string, toneOverride?: string) => void;
  loading: boolean;
}

const PRESETS = [
  {
    label: "Google · Distributed Systems",
    company: "google",
    text: `Software Engineer, Distributed Systems - Google
Location: Mountain View, CA / Bengaluru, India

Responsibilities:
- Build high-scale distributed backend systems and asynchronous microservices handling high RPS.
- Optimize machine learning pipelines for latency, SSIM/PSNR accuracy, and memory footprint.
- Collaborate with engineering leads to design production-grade REST and RPC services.

Qualifications:
- Bachelor's degree in Computer Science or equivalent.
- Experience with Python, PyTorch, FastAPI, Docker, and distributed systems.
- Experience with RAG, vector search, or database performance optimization.`,
  },
  {
    label: "Amazon · AWS Cloud Backend",
    company: "amazon",
    text: `Senior Backend Engineer - Amazon AWS
Location: Seattle, WA / Hyderabad, India

Responsibilities:
- Architect high-throughput distributed microservices on AWS infrastructure.
- Build resilient backend systems using Python, FastAPI, Docker, and PostgreSQL.
- Drive latency reduction, high concurrency, and customer-first operational metrics.

Requirements:
- Strong proficiency in Python, FastAPI, Microservices, and Cloud infrastructure.
- Proven track record of shipping production code with automated tests and CI/CD.`,
  },
  {
    label: "Startup · Full-Stack AI Engineer",
    company: "startup",
    text: `Founding AI Engineer - NextGen Agents (YC Backed)
Location: Remote / Bengaluru

Looking for a relentless builder who moves fast:
- Build agentic AI workflows with LangGraph, PyTorch, and RAG architectures.
- Ship end-to-end full-stack applications with FastAPI, React, and vector databases.
- Grand Champion hackathon winner or top-tier open source contributor preferred.`,
  },
];

export function JDInput({ onGenerate, loading }: JDInputProps) {
  const [jdText, setJdText] = useState("");
  const [companyOverride, setCompanyOverride] = useState("");
  const [toneOverride, setToneOverride] = useState("");

  const handlePreset = (preset: typeof PRESETS[0]) => {
    setJdText(preset.text);
    setCompanyOverride(preset.company);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!jdText.trim()) return;
    onGenerate(jdText, companyOverride || undefined, toneOverride || undefined);
  };

  return (
    <div className="flex flex-col gap-4 p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            Target Job Description
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Paste any job posting or select a quick role preset
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePreset(p)}
              className="text-xs px-2.5 py-1 rounded-md border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 transition-colors"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <textarea
        value={jdText}
        onChange={(e) => setJdText(e.target.value)}
        placeholder="Paste full job description, qualifications, and responsibilities here..."
        className="w-full h-44 p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 text-xs font-mono text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none leading-relaxed"
      />

      <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-zinc-600 dark:text-zinc-400">
            <span>DNA:</span>
            <select
              value={companyOverride}
              onChange={(e) => setCompanyOverride(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none"
            >
              <option value="">Auto-Detect DNA</option>
              <option value="google">Google (Research/Analytical)</option>
              <option value="amazon">Amazon (Metrics/Ownership)</option>
              <option value="microsoft">Microsoft (Enterprise/Scale)</option>
              <option value="startup">Startup (Speed/Autonomy)</option>
              <option value="research">Research (Publications/SSIM)</option>
              <option value="generic">Generic Industry Standard</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-zinc-600 dark:text-zinc-400">
            <span>Tone:</span>
            <select
              value={toneOverride}
              onChange={(e) => setToneOverride(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none"
            >
              <option value="">Default Style DNA</option>
              <option value="metric-heavy, quantitative">Metric-Dense & Numbers</option>
              <option value="engineering-first, technical">Deep Systems & Code</option>
              <option value="leadership, ownership">Execution & Leadership</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || !jdText.trim()}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 text-white font-medium text-xs transition-all shadow-sm flex items-center gap-2 cursor-pointer"
        >
          {loading ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Synthesizing Tailored Resume...</span>
            </>
          ) : (
            <>
              <span>⚡ Generate Tailored Resume</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
