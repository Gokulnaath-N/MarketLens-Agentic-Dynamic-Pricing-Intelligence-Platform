/**
 * TypeScript API contracts matching MarketLens AI backend Pydantic models.
 */

export interface HealthResponse {
  status: string
  app_name: string
  version: string
  timestamp_utc: string
}

export interface ModuleStatus {
  name: string
  available: boolean
  status_label: string
  details?: string
}

export interface SystemStatusResponse {
  health: string
  backend_version: string
  environment: string
  timestamp_utc: string
  modules: ModuleStatus[]
  dataset_summary: Record<string, any>
  models_summary: any
  phase5_ablation_summary: Record<string, any>
}

export interface DatasetFileItem {
  filename: string
  file_path: string
  detected_format: string
  byte_size: number
  sha256_hash: string
  validation_status: string
}

export interface DatasetRecord {
  dataset_id: string
  name: string
  publisher: string
  license_name: string
  license_url: string
  acquired_at_utc: string
  citation: string
  files: DatasetFileItem[]
  has_profile: boolean
}

export interface ColumnProfile {
  detected_type?: string
  null_count?: number
  null_ratio?: number
  unique_count?: number
  mean?: number
  std?: number
  min?: any
  max?: any
  quantiles?: Record<string, number>
}

export interface DatasetProfileSummary {
  dataset_id: string
  source_file: string
  profiled_at_utc: string
  row_count: number
  column_count: number
  min_timestamp?: string
  max_timestamp?: string
  detected_target_column?: string
  detected_price_column?: string
  detected_time_column?: string
  detected_identifier_columns: string[]
  suitability_for_forecasting: string
  data_quality_issues: string[]
  column_profiles: Record<string, ColumnProfile>
}

export interface ModelMetricItem {
  model_name: string
  mae: number
  rmse: number
  wape: number
  r2: number
  evaluation_split: string
}

export interface ForecastModelListResponse {
  models: string[]
  target_column: string
  frequency: string
  evaluation_artifacts_exist: boolean
  metrics: ModelMetricItem[]
  predictions_preview: Array<Record<string, any>>
}

export interface LiveForecastRequest {
  product_id: string
  candidate_price: number
  horizon_weeks?: number
  elasticity?: number
  base_demand?: number
  reference_price?: number
}

export interface LiveForecastResponse {
  product_id: string
  candidate_price: number
  predicted_demand: number
  expected_revenue: number
  horizon_weeks: number
  model_type: string
  is_synthetic: boolean
  explanation: string
}

export interface CompetitorPriceItem {
  product_id: string
  competitor_name: string
  observed_price: number
  currency: string
  observed_date: string
  source_type: string
}

export interface ReviewSentimentItem {
  review_id: string
  product_id: string
  sentiment_label: string
  sentiment_score: number
  rating?: number
  aspects: string[]
  complaint_categories: string[]
  praise_categories: string[]
  summary: string
  evidence_excerpt?: string
}

export interface MarketIntelligenceSummary {
  total_reviews_analyzed: number
  sentiment_breakdown: Record<string, number>
  top_aspects: Array<{ aspect: string; sentiment: string; mentions: number }>
  competitors_monitored: string[]
  recent_competitor_observations: CompetitorPriceItem[]
  recent_reviews: ReviewSentimentItem[]
  is_live_feed_available: boolean
  source_attribution: string
}

export type OptimizationObjective = 'revenue' | 'profit'

export interface OptimizationRequest {
  product_id: string
  current_price: number
  price_min: number
  price_max: number
  price_step?: number
  num_candidates?: number
  objective: OptimizationObjective
  unit_cost?: number
  min_gross_margin?: number
  max_price_change_pct?: number
  competitor_reference_price?: number
  max_competitor_price_premium_pct?: number
  currency?: string
  forecast_horizon?: number
  demand_context?: Record<string, any>
  is_synthetic?: boolean
}

export interface CandidateEvaluation {
  candidate_price: number
  predicted_demand: number
  expected_revenue: number
  estimated_profit?: number
  gross_margin?: number
  is_within_model_support: boolean
  is_feasible: boolean
  rejection_reasons: string[]
  warnings: string[]
}

export interface OptimizationResult {
  product_id: string
  forecast_horizon: number
  objective: OptimizationObjective
  currency: string
  current_price: number
  recommended_price?: number
  predicted_demand?: number
  expected_revenue?: number
  estimated_profit?: number
  gross_margin?: number
  status: string
  total_candidates: number
  feasible_candidates: number
  is_feasible: boolean
  is_within_model_support: boolean
  human_approval_required: boolean
  candidates: CandidateEvaluation[]
  explanation: string
  warnings: string[]
  model_metadata: Record<string, any>
  is_synthetic: boolean
  created_at_utc: string
}

export interface ExperimentRunItem {
  run_id: string
  timestamp_utc: string
  ablation_type: string
  description: string
  features_count: number
  mae: number
  rmse: number
  wape: number
  r2: number
  delta_wape_vs_baseline: number
  delta_mae_vs_baseline: number
}
