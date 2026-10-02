"use client";

interface InterviewScoreProps {
  interviewProbability?: number;
  atsScore?: number;
}

export function InterviewScore({ interviewProbability = 0, atsScore = 0 }: InterviewScoreProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-900/40 bg-emerald-50/50 dark:bg-emerald-950/20">
        <span className="text-xs uppercase font-bold tracking-wider text-emerald-700 dark:text-emerald-400">
          Interview Probability
        </span>
        <div className="text-3xl font-bold text-emerald-800 dark:text-emerald-300 mt-1">
          {interviewProbability > 0 ? `${interviewProbability}%` : "—"}
        </div>
      </div>
      <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900/40 bg-blue-50/50 dark:bg-blue-950/20">
        <span className="text-xs uppercase font-bold tracking-wider text-blue-700 dark:text-blue-400">
          ATS Match Score
        </span>
        <div className="text-3xl font-bold text-blue-800 dark:text-blue-300 mt-1">
          {atsScore > 0 ? `${atsScore}/100` : "—"}
        </div>
      </div>
    </div>
  );
}
