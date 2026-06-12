// Shared API types mirroring the backend Pydantic schemas.

export type UploadType = "followers" | "visitors" | "content" | "unknown";
export type UploadStatus = "pending" | "parsed" | "duplicate" | "failed";

export type RangePreset =
  | "last_7" | "last_30" | "last_90"
  | "mtd" | "qtd" | "ytd" | "all_time" | "custom";

export type ComparisonMode = "previous_period" | "same_period_last_year" | "none";

export interface Upload {
  id: string;
  filename: string;
  upload_type: UploadType;
  status: UploadStatus;
  detected_format: string | null;
  rows_ingested: number;
  size_bytes: number;
  created_at: string;
  error: string | null;
}

export interface ValidationReport {
  detected_type: UploadType;
  confidence: number;
  detected_format: string;
  detected_headers: Record<string, string[]>;
  sheet_headers?: Record<string, string[]>;
  warnings: string[];
  rows_ingested: number;
  metrics: number;
  posts: number;
  demographics: number;
}

export interface UploadResult {
  upload: Upload;
  report: ValidationReport | null;
  duplicate: boolean;
}

export interface TimePoint { date: string; value: number; }
export interface Series { metric: string; points: TimePoint[]; }
export interface CategoryValue { category: string; value: number; }

export interface KPI {
  key: string;
  label: string;
  value: number | null;
  previous: number | null;
  delta_pct: number | null;
  sparkline: number[];
  unit: "count" | "percent";
}

export interface TopPost {
  post_url: string;
  title: string | null;
  post_type: string | null;
  impressions: number;
  engagement_rate: number | null;
}

export interface OverviewResponse {
  range_start: string;
  range_end: string;
  kpis: KPI[];
  top_post: TopPost | null;
  top_posts: TopPost[];
}


export interface FollowersResponse {
  daily: Series;
  rolling_7d: Series;
  cumulative: Series;
  demographics: Record<string, CategoryValue[]>;
}

export interface VisitorsResponse {
  page_views: Series;
  unique_visitors: Series;
  section_views: CategoryValue[];
  device_split: CategoryValue[];
  followers_per_unique_visitor: number | null;
}

export interface PostRow {
  date: string | null;
  post_type: string | null;
  impressions: number;
  ctr: number | null;
  engagement_rate: number | null;
  reactions: number;
  comments: number;
  reposts: number;
  post_url: string;
  title: string | null;
}

export interface ContentResponse {
  impressions_over_time: Series;
  engagement_over_time: Series;
  posts: PostRow[];
  by_post_type: CategoryValue[];
  by_day_of_week: CategoryValue[];
  by_hour_bucket: CategoryValue[];
}

export interface Insight {
  rule_id: string;
  title: string;
  evidence: string;
  impact_score: number;
  confidence_score: number;
  recommendation: string;
  supporting_metrics: Record<string, number>;
}

export interface InsightsResponse {
  range_start: string;
  range_end: string;
  insights: Insight[];
}
