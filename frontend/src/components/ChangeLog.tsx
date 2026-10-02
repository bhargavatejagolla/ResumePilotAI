"use client";

interface ChangeLogProps {
  changes?: string[];
}

export function ChangeLog({ changes = [] }: ChangeLogProps) {
  return (
    <div className="p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
      <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-2">
        Tailoring & Change Log
      </h3>
      {changes.length === 0 ? (
        <p className="text-xs text-zinc-500">No modifications logged yet.</p>
      ) : (
        <ul className="space-y-1 text-xs text-zinc-700 dark:text-zinc-300">
          {changes.map((item, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-emerald-500 font-bold">✓</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
