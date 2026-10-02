"use client";

interface ResumePreviewProps {
  pdfBase64?: string | null;
}

export function ResumePreview({ pdfBase64 }: ResumePreviewProps) {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm min-h-[400px]">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          PDF Preview
        </h2>
        {pdfBase64 && (
          <button className="px-3 py-1.5 rounded-md bg-zinc-800 text-white text-xs font-medium hover:bg-zinc-700">
            Download PDF
          </button>
        )}
      </div>
      <div className="flex-1 flex items-center justify-center border border-dashed border-zinc-300 dark:border-zinc-700 rounded-lg bg-zinc-50 dark:bg-zinc-950 p-6 text-zinc-500 text-sm">
        {pdfBase64 ? (
          <iframe
            src={`data:application/pdf;base64,${pdfBase64}`}
            className="w-full h-full min-h-[500px] rounded"
          />
        ) : (
          "Your pixel-perfect tailored resume PDF preview will appear here."
        )}
      </div>
    </div>
  );
}
