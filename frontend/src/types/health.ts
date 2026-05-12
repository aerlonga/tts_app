export interface HealthResponse {
  status: string;
}

export interface StorageStatusItem {
  path: string;
  exists: boolean;
  is_dir: boolean;
  writable: boolean;
}

export interface ExternalServiceStatus {
  name: string;
  configured: boolean;
  detail: string;
}

export interface CostControlStatus {
  usage_routes_available: boolean;
  ai_usage_logging_ready: boolean;
  pricing_configured: boolean;
  top_risk: string;
}

export interface HealthDetailsResponse {
  status: string;
  python_version: string;
  database_url: string;
  database_reachable: boolean;
  ffmpeg_available: boolean;
  storage: StorageStatusItem[];
  external_services: ExternalServiceStatus[];
  cost_control: CostControlStatus;
}
