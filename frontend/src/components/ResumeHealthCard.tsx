"use client";

import { ResumeHealthReport } from "@/lib/api";

interface ResumeHealthCardProps {
  report: ResumeHealthReport | null;
  candidateName?: string;
}

export function ResumeHealthCard({ report, candidateName }: ResumeHealthCardProps) {
  if (!report) return null;

  const scoreColor =
    report.overall_score >= 80
      ? "text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/20"
      : report.overall_score >= 60
      ? "text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/20"
      : "text-rose-700 dark:text-rose-400 border-rose-300 dark:border-rose-800 bg-rose-50/50 dark:bg-rose-950/20";

  return (
    <div className="flex flex-col gap-3.5 p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide">
              Resume Diagnostic & Health Audit
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-semibold border border-blue-200 dark:border-blue-800">
              Pre-Tailoring Coach
            </span>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            Diagnostic report for <b>{candidateName || "Uploaded Resume"}</b> before JD tailoring
          </p>
        </div>

        <div className={`px-3 py-1.5 rounded-xl border text-center ${scoreColor}`}>
          <span className="text-[10px] uppercase font-bold block">Base Score</span>
          <span className="text-xl font-extrabold">{report.overall_score}</span>
          <span className="text-[10px] font-normal">/100</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-2.5 pt-1 text-xs">
        <div className="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-950/50">
          <span className="text-[10px] text-zinc-400 uppercase font-semibold block">
            Metric Density
          </span>
          <span className="text-sm font-bold text-zinc-900 dark:text-zinc-100">
            {report.metric_bullets_count} / {report.total_bullets}
          </span>
          <span className="text-[10px] text-zinc-500 block">
            ({Math.round(report.metric_density * 100)}% bullets quantified)
          </span>
        </div>

        <div className="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-950/50">
          <span className="text-[10px] text-zinc-400 uppercase font-semibold block">
            Weak Verbs
          </span>
          <span className={`text-sm font-bold ${report.weak_verbs_count > 0 ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400"}`}>
            {report.weak_verbs_count} flagged
          </span>
          <span className="text-[10px] text-zinc-500 block">
            Passive opening verbs
          </span>
        </div>

        <div className="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-950/50">
          <span className="text-[10px] text-zinc-400 uppercase font-semibold block">
            Unevidenced Skills
          </span>
          <span className={`text-sm font-bold ${report.unevidenced_skills.length > 0 ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400"}`}>
            {report.unevidenced_skills.length} unproven
          </span>
          <span className="text-[10px] text-zinc-500 block">
            Skills with no project link
          </span>
        </div>
      </div>

      {/* Top Prioritized Improvements */}
      {report.top_improvements.length > 0 && (
        <div className="p-3 rounded-xl bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 text-xs">
          <span className="font-semibold text-amber-900 dark:text-amber-300 block mb-1">
            Top Prioritized Improvements:
          </span>
          <ul className="space-y-1 text-amber-800 dark:text-amber-200/90 text-[11px]">
            {report.top_improvements.map((imp, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <span className="text-amber-600 dark:text-amber-400 font-bold">#{idx + 1}</span>
                <span>{imp}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
