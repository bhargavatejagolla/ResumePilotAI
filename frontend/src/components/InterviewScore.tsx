"use client";

import { VerificationResult } from "@/lib/api";

interface InterviewScoreProps {
  verification?: VerificationResult | null;
  companyType?: string;
}

export function InterviewScore({ verification, companyType }: InterviewScoreProps) {
  if (!verification) {
    return (
      <div className="p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm flex flex-col items-center justify-center text-center">
        <div className="w-12 h-12 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-xl mb-3">
          📊
        </div>
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Awaiting Job Description
        </h3>
        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-sm">
          Paste a JD and click generate to calculate your calibrated interview probability and ATS breakdown.
        </p>
      </div>
    );
  }

  const { ats, interview_prob } = verification;

  return (
    <div className="flex flex-col gap-4 p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            Intelligence & Fit Metrics
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Calibrated for {companyType ? companyType.toUpperCase() : "Target Role"}
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
          {interview_prob.tier}
        </span>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/40 dark:bg-emerald-950/20">
          <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-700 dark:text-emerald-400">
            Interview Probability
          </span>
          <div className="text-2xl font-bold text-emerald-800 dark:text-emerald-300 mt-0.5">
            {interview_prob.percentage}%
          </div>
          <span className="text-[11px] text-emerald-600 dark:text-emerald-400">
            Calibrated hire score
          </span>
        </div>

        <div className="p-3.5 rounded-xl border border-blue-200 dark:border-blue-900/40 bg-blue-50/40 dark:bg-blue-950/20">
          <span className="text-[10px] uppercase font-bold tracking-wider text-blue-700 dark:text-blue-400">
            Total ATS Score
          </span>
          <div className="text-2xl font-bold text-blue-800 dark:text-blue-300 mt-0.5">
            {ats.total_score}
            <span className="text-xs font-normal text-blue-600 dark:text-blue-400">/100</span>
          </div>
          <span className="text-[11px] text-blue-600 dark:text-blue-400">
            Composite ATS health
          </span>
        </div>

        <div className="p-3.5 rounded-xl border border-indigo-200 dark:border-indigo-900/40 bg-indigo-50/40 dark:bg-indigo-950/20">
          <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-700 dark:text-indigo-400">
            Keyword Match
          </span>
          <div className="text-2xl font-bold text-indigo-800 dark:text-indigo-300 mt-0.5">
            {ats.keyword_match_score}%
          </div>
          <span className="text-[11px] text-indigo-600 dark:text-indigo-400">
            {ats.matched_keywords.length} terms detected
          </span>
        </div>

        <div className="p-3.5 rounded-xl border border-purple-200 dark:border-purple-900/40 bg-purple-50/40 dark:bg-purple-950/20">
          <span className="text-[10px] uppercase font-bold tracking-wider text-purple-700 dark:text-purple-400">
            Metric Density
          </span>
          <div className="text-2xl font-bold text-purple-800 dark:text-purple-300 mt-0.5">
            {ats.metric_density_score}%
          </div>
          <span className="text-[11px] text-purple-600 dark:text-purple-400">
            Quantified achievements
          </span>
        </div>
      </div>

      {/* Keywords Breakdown */}
      <div className="flex flex-col gap-2 pt-1">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-zinc-800 dark:text-zinc-200">
            Matched Keywords ({ats.matched_keywords.length})
          </span>
          {ats.missing_keywords.length > 0 && (
            <span className="text-amber-600 dark:text-amber-400 font-medium">
              {ats.missing_keywords.length} gaps flagged
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
          {ats.matched_keywords.map((kw, i) => (
            <span
              key={i}
              className="text-[11px] px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-700"
            >
              ✓ {kw}
            </span>
          ))}
          {ats.missing_keywords.slice(0, 5).map((kw, i) => (
            <span
              key={i}
              className="text-[11px] px-2 py-0.5 rounded-md bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
            >
              ⚠ {kw}
            </span>
          ))}
        </div>
      </div>

      {/* Strengths & Recommendation */}
      {interview_prob.recommendation && (
        <div className="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 text-xs">
          <span className="font-semibold text-zinc-900 dark:text-zinc-100 block mb-1">
            Recommendation:
          </span>
          <p className="text-zinc-600 dark:text-zinc-300">
            {interview_prob.recommendation}
          </p>
        </div>
      )}
    </div>
  );
}
