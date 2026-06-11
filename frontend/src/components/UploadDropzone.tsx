import { useRef, useState } from "react";
import { api } from "../services/api";
import type { UploadResult, UploadType } from "../types";

const TYPES: { value: UploadType | ""; label: string }[] = [
  { value: "", label: "Auto-detect" },
  { value: "followers", label: "Followers" },
  { value: "visitors", label: "Visitors" },
  { value: "content", label: "Content" },
];

export function UploadDropzone({ onUploaded }: { onUploaded: (r: UploadResult) => void }) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [override, setOverride] = useState<UploadType | "">("");
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || !files.length) return;
    setBusy(true);
    setError(null);
    try {
      for (const file of Array.from(files)) {
        const result = await api.uploadFile(file, override || undefined);
        onUploaded(result);
      }
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div>
      <div className="mb-2 flex items-center gap-2">
        <label className="text-xs text-slate-500">Type override:</label>
        <select
          value={override}
          onChange={(e) => setOverride(e.target.value as UploadType | "")}
          className="rounded border border-slate-200 px-2 py-1 text-xs"
        >
          {TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition ${
          dragging ? "border-brand bg-brand-light" : "border-slate-300 bg-white hover:border-brand"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xls,.xlsx"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <p className="text-sm font-medium text-slate-600">
          {busy ? "Uploading…" : "Drag & drop LinkedIn exports here, or click to browse"}
        </p>
        <p className="mt-1 text-xs text-slate-400">Followers · Visitors · Content (.xls / .xlsx)</p>
      </div>
      {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
    </div>
  );
}
