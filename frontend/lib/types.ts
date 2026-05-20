export interface PlayerSummary {
  player_id: string;
  name: string;
  primary_position: string;
  team: string;
  versatility_score: number;
  num_matches: number;
  photo_url?: string | null;
  team_logo_url?: string | null;
}

export interface PlayerDetail extends PlayerSummary {
  num_distinct_positions: number;
  position_distribution: Record<string, number>;
}

export interface Candidate extends PlayerSummary {
  rank: number;
  similarity: number;
  attacker_rank?: number;
}

export interface UpgradeSpec {
  key: string;
  label: string;
  description: string;
  applies_to: "onball" | "offball";
}

export interface UpgradeCatalog {
  onball: UpgradeSpec[];
  offball: UpgradeSpec[];
}

export interface FilterCatalog {
  coming_soon: string[];
  [key: string]: unknown;
}

export interface HealthResponse {
  status: "ok";
  engine_loaded: boolean;
  engine_state: "warming" | "ready" | "unavailable";
  engine_message: string | null;
  uptime_seconds: number;
}

export type UpgradeRequest = string[] | Record<string, number>;

export interface SearchRequest {
  sources: string[];
  upgrades?: UpgradeRequest;
  upgrade_intensity?: number;
  top_k?: number;
  filters?: Record<string, unknown>;
  exclude_sources?: boolean;
  seed?: number;
}

export interface SearchResponse {
  query: {
    sources: PlayerSummary[];
    upgrades: UpgradeRequest;
    upgrade_intensity: number;
    filters: Record<string, unknown>;
    seed: number;
  };
  candidates: Candidate[];
  warnings: string[];
}

export interface JobAcceptedResponse {
  job_id: string;
  status: "pending";
}

export interface JobRecord {
  job_id: string;
  status: "pending" | "running" | "done" | "error";
  created_at: string;
  updated_at: string;
  result: SearchResponse | null;
  error: string | null;
}

export type Verdict = "EXCELLENT" | "STRONG" | "ACCEPTABLE" | "MARGINAL" | "FAIL";

export interface ManeValidationResponse extends SearchResponse {
  mane_rank: number | null;
  verdict: Verdict;
  verdict_description: string;
  filtered_defender_count: number;
}

export interface PlayerHeatmap {
  counts: number[];   // length 18, row-major from top-left, attacking L→R
  total: number;
  num_x: number;      // 6
  num_y: number;      // 3
  num_zones: number;  // 18
}

export interface HeatmapSlice {
  counts: number[];
  total: number;
  label: string;
  source_names?: string[];
  player_id?: string | null;
}

export interface ManeHeatmapResponse {
  pool: HeatmapSlice;
  mane: HeatmapSlice;
  num_x: number;
  num_y: number;
  num_zones: number;
}
