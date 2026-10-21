"use client";

import { BulletDiff, ProjectDecision } from "@/lib/api";

interface ChangeLogProps {
  bulletDiffs?: BulletDiff[];
  projectDecisions?: ProjectDecision[];
}

export function ChangeLog({ bulletDiffs = [], projectDecisions = [] }: ChangeLogProps) {
  if (bulletDiffs.length === 0 && projectDecisions.length === 0) {
    return null;
  }

  const modifiedBullets = bulletDiffs.filter((b) => b.changed);

  return (
    <div className="flex flex-col gap-4 p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            Tailoring Truth Engine & Audit Log
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            100% Truth-Verified · Zero Metric Hallucinations
          </p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 font-mono text-zinc-600 dark:text-zinc-300">
          {modifiedBullets.length} of {bulletDiffs.length} bullets polished
        </span>
      </div>

      {/* Project Selection Rationale */}
      {projectDecisions.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Selected Projects & Evidence
          </span>
          <div className="grid grid-cols-1 gap-2">
            {projectDecisions.map((proj, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-950/40 text-xs"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {proj.project_name}
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300">
                    SELECTED (Rank #{idx + 1})
                  </span>
                </div>
                <ul className="space-y-0.5 text-zinc-600 dark:text-zinc-400 text-[11px]">
                  {proj.reasons.map((r, rIdx) => (
                    <li key={rIdx} className="flex items-start gap-1.5">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bullet Point Modifications */}
      {bulletDiffs.length > 0 && (
        <div className="space-y-2 pt-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Bullet Rewrites & Metric Guard
          </span>
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {bulletDiffs.map((diff, i) => (
              <div
                key={i}
                className="p-3 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-950/40 text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100 text-[11px]">
                    {diff.entity}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono text-zinc-400">
                      {diff.source}
                    </span>
                    {diff.changed ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-semibold">
                        POLISHED
                      </span>
                    ) : diff.rejection ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 font-semibold">
                        GUARD ENFORCED ({diff.rejection})
                      </span>
                    ) : (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                        ORIGINAL KEPT
                      </span>
                    )}
                  </div>
                </div>

                {diff.changed ? (
                  <div className="space-y-1">
                    <div className="text-zinc-400 line-through text-[11px] bg-red-50/40 dark:bg-red-950/20 p-1.5 rounded">
                      {diff.original}
                    </div>
                    <div className="text-zinc-900 dark:text-zinc-100 font-medium text-[11px] bg-emerald-50/40 dark:bg-emerald-950/20 p-1.5 rounded">
                      {diff.rewritten}
                    </div>
                  </div>
                ) : (
                  <p className="text-zinc-700 dark:text-zinc-300 text-[11px]">
                    {diff.original}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
