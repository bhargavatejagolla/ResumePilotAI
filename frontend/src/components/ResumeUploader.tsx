"use client";

import { useState, useRef } from "react";
import { uploadResumeFile, UploadResumeResponse } from "@/lib/api";

interface ResumeUploaderProps {
  activeResumeId: string;
  candidateName: string;
  onUploaded: (data: UploadResumeResponse) => void;
  onSelectMaster: () => void;
}

export function ResumeUploader({
  activeResumeId,
  candidateName,
  onUploaded,
  onSelectMaster,
}: ResumeUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
      return;
    }

    try {
      setUploading(true);
      setError(null);
      const res = await uploadResumeFile(file);
      onUploaded(res);
    } catch (err: any) {
      console.error("Upload error:", err);
      setError(err.message || "Failed to parse and index resume.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const isMaster = activeResumeId === "saketh" || activeResumeId === "default";

  return (
    <div className="flex flex-col gap-3 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide">
            Source Resume Profile
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Active: <span className="font-semibold text-zinc-900 dark:text-zinc-100">{candidateName}</span> ({activeResumeId})
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl text-xs">
          <button
            type="button"
            onClick={onSelectMaster}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
              isMaster
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-xs"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
            }`}
          >
            ⭐ Master Profile
          </button>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
              !isMaster
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-xs"
                : "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100"
            }`}
          >
            ⬆ Upload Resume (PDF)
          </button>
        </div>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".pdf"
        className="hidden"
      />

      {uploading && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900/40 text-xs text-blue-700 dark:text-blue-300">
          <span className="w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span>Parsing PDF layout, indexing in ChromaDB, and running health diagnostic...</span>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 text-xs text-rose-700 dark:text-rose-300 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-bold">✕</button>
        </div>
      )}
    </div>
  );
}
