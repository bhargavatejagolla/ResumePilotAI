"use client";

interface JDInputProps {
  onGenerate?: (jdText: string) => void;
  loading?: boolean;
}

export function JDInput({ onGenerate, loading }: JDInputProps) {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        Target Job Description
      </h2>
      <textarea
        placeholder="Paste the target job description or requirements here..."
        className="w-full h-48 p-3 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 text-sm text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans resize-none"
      />
      <button
        disabled={loading}
        className="self-end px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium text-sm transition-colors shadow-sm"
      >
        {loading ? "Generating Plan..." : "Generate Tailored Resume"}
      </button>
    </div>
  );
}
