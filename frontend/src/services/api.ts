import type {
  BirdsEyeResponse,
  ContentResponse,
  FollowersResponse,
  InsightsResponse,
  OverviewResponse,
  Upload,
  UploadResult,
  VisitorsResponse,
} from "../types";

const BASE = "/api";

export interface RangeQuery {
  preset: string;
  start?: string;
  end?: string;
  compare?: string;
}

function qs(q: RangeQuery): string {
  const params = new URLSearchParams();
  params.set("preset", q.preset);
  if (q.start) params.set("start", q.start);
  if (q.end) params.set("end", q.end);
  if (q.compare) params.set("compare", q.compare);
  return params.toString();
}

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listUploads: () => getJSON<Upload[]>(`${BASE}/uploads`),

  uploadFile: async (file: File, overrideType?: string): Promise<UploadResult> => {
    const form = new FormData();
    form.append("file", file);
    if (overrideType) form.append("override_type", overrideType);
    const res = await fetch(`${BASE}/uploads`, { method: "POST", body: form });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `Upload failed: ${res.status}`);
    }
    return res.json();
  },

  overview: (q: RangeQuery) => getJSON<OverviewResponse>(`${BASE}/dashboard/overview?${qs(q)}`),
  followers: (q: RangeQuery) => getJSON<FollowersResponse>(`${BASE}/dashboard/followers?${qs(q)}`),
  visitors: (q: RangeQuery) => getJSON<VisitorsResponse>(`${BASE}/dashboard/visitors?${qs(q)}`),
  content: (q: RangeQuery) => getJSON<ContentResponse>(`${BASE}/dashboard/content?${qs(q)}`),
  insights: (q: RangeQuery) => getJSON<InsightsResponse>(`${BASE}/insights?${qs(q)}`),
  birdseye: (q: RangeQuery) => getJSON<BirdsEyeResponse>(`${BASE}/birdseye?${qs(q)}`),
  deleteUploads: async (): Promise<void> => {
    const res = await fetch(`${BASE}/uploads`, { method: "DELETE" });
    if (!res.ok) {
      let msg = `Delete failed: ${res.status}`;
      try {
        const detail = await res.json();
        if (detail?.detail) msg = detail.detail;
      } catch {
        // 204 or empty body — ignore parse error
      }
      throw new Error(msg);
    }
  },
};

