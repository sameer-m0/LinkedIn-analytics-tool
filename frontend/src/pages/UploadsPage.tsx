import { useState } from "react";
import { Card } from "../components/Card";
import { UploadDropzone } from "../components/UploadDropzone";
import { useFetch } from "../hooks/useFetch";
import { api } from "../services/api";
import type { UploadResult } from "../types";
import { formatNumber } from "../utils/format";

const STATUS_STYLES: Record<string, string> = {
  parsed: "bg-emerald-100 text-emerald-700",
  duplicate: "bg-amber-100 text-amber-700",
  failed: "bg-rose-100 text-rose-700",
  pending: "bg-slate-100 text-slate-600",
};

export function UploadsPage() {
  const { data, loading, reload } = useFetch(() => api.listUploads(), []);
  const [lastResult, setLastResult] = useState<UploadResult | null>(null);

  return (
    <div className="space-y-6">
      <Card title="Upload exports">
        <UploadDropzone
          onUploaded={(r) => {
            setLastResult(r);
            reload();
          }}
        />
      </Card>

      {lastResult && (
        <Card title="Latest upload — validation report">
          {lastResult.duplicate ? (
            <p className="text-sm text-amber-700">
              Identical file already ingested ({lastResult.upload.filename}). No changes applied.
            </p>
          ) : lastResult.report ? (
            <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <Stat label="Detected type" value={lastResult.report.detected_type} />
              <Stat label="Confidence" value={`${(lastResult.report.confidence * 100).toFixed(0)}%`} />
              <Stat label="Format" value={lastResult.report.detected_format} />
              <Stat label="Rows ingested" value={formatNumber(lastResult.report.rows_ingested)} />
              <Stat label="Metrics" value={formatNumber(lastResult.report.metrics)} />
              <Stat label="Posts" value={formatNumber(lastResult.report.posts)} />
              <Stat label="Demographics" value={formatNumber(lastResult.report.demographics)} />
              <Stat label="Warnings" value={formatNumber(lastResult.report.warnings.length)} />
            </div>
          ) : lastResult.upload.error ? (
            <p className="text-sm text-rose-600">Failed: {lastResult.upload.error}</p>
          ) : null}
        </Card>
      )}

      <Card title="Upload history">
        {loading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-xs uppercase tracking-wide text-slate-400">
                <th className="py-2 pr-3">File</th>
                <th className="py-2 pr-3">Type</th>
                <th className="py-2 pr-3">Status</th>
                <th className="py-2 pr-3 text-right">Rows</th>
                <th className="py-2 pr-3">Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {(data || []).map((u) => (
                <tr key={u.id} className="border-b last:border-0">
                  <td className="py-2 pr-3 font-medium text-slate-700">{u.filename}</td>
                  <td className="py-2 pr-3">{u.upload_type}</td>
                  <td className="py-2 pr-3">
                    <span className={`rounded px-2 py-0.5 text-xs ${STATUS_STYLES[u.status] || ""}`}>{u.status}</span>
                  </td>
                  <td className="py-2 pr-3 text-right">{formatNumber(u.rows_ingested)}</td>
                  <td className="py-2 pr-3 text-slate-500">{new Date(u.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {(data || []).length === 0 && (
                <tr>
                  <td colSpan={5} className="py-4 text-center text-slate-400">No uploads yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="mt-0.5 font-semibold text-slate-800">{value}</p>
    </div>
  );
}
