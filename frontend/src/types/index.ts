export enum ViolationType {
  Scam = 'scam',
  Harassment = 'harassment',
  FakeProfile = 'fake_profile',
  SelfHarm = 'self_harm',
  IllegalActivity = 'illegal_activity',
  ChildSafety = 'child_safety',
  BotFarm = 'bot_farm',
  RepeatOffender = 'repeat_offender',
  Unknown = 'unknown',
}

export enum CaseStatus {
  New = 'new',
  Investigating = 'investigating',
  PendingReview = 'pending_review',
  InReview = 'in_review',
  Resolved = 'resolved',
  Escalated = 'escalated',
  Appealed = 'appealed',
}

export enum Priority {
  Critical = 'critical',
  High = 'high',
  Medium = 'medium',
  Low = 'low',
}

export enum EnforcementAction {
  Warning = 'warning',
  ContentRemoval = 'content_removal',
  RateLimit = 'rate_limit',
  TempSuspension = 'temp_suspension',
  PermanentBan = 'permanent_ban',
}

export enum ContentSeverity {
  Low = 'low',
  Medium = 'medium',
  High = 'high',
  Extreme = 'extreme',
}

export enum DecisionType {
  ApproveAction = 'approve_action',
  CustomAction = 'custom_action',
  Dismiss = 'dismiss',
  Escalate = 'escalate',
}

export enum SanitizationLevel {
  LabelsOnly = 'labels_only',
  Blurred = 'blurred',
  Full = 'full',
}

export interface Case {
  case_id: string
  user_id: string
  status: CaseStatus
  violation_type: ViolationType
  confidence_score: number
  content_severity: ContentSeverity
  created_at: string
  updated_at: string
  audit_trail_ids: string[]
  trigger_source?: string
  assigned_reviewer?: string
}

export interface EvidencePackage {
  case_id: string
  user_id: string
  profile_metadata?: ProfileMetadata
  message_history?: MessageHistory
  previous_reports?: PreviousReport[]
  content_analysis?: ContentAnalysis
  image_analysis?: ImageAnalysis
  cross_platform_intelligence?: CrossPlatformMatch
  sources_unavailable?: string[]
  assembled_at: string
}

export interface ProfileMetadata {
  user_id: string
  display_name?: string
  account_age_days?: number
  profile_completeness?: number
  photo_count?: number
  verification_status?: string
}

export interface MessageHistory {
  messages: Message[]
  total_count: number
}

export interface Message {
  message_id: string
  content: string
  sent_at: string
  recipient_id?: string
  flagged?: boolean
}

export interface PreviousReport {
  report_id: string
  reporter_id: string
  reason: string
  created_at: string
}

export interface ContentAnalysis {
  scam_indicators: Indicator[]
  threat_indicators: Indicator[]
  crisis_indicators: Indicator[]
  sentiment?: SentimentResult
}

export interface Indicator {
  type: string
  pattern: string
  severity: string
  context?: string
}

export interface SentimentResult {
  overall: string
  manipulation_score: number
  aggression_score: number
}

export interface ImageAnalysis {
  profile_images: ImageResult[]
}

export interface ImageResult {
  image_id: string
  is_ai_generated?: boolean
  is_stock_photo?: boolean
  reverse_search_matches?: number
}

export interface CrossPlatformMatch {
  match_type: string
  confidence: number
  source_platform: string
  ban_reason?: string
}

export interface ReviewQueueItem {
  queue_id: string
  case_id: string
  user_id: string
  violation_type: ViolationType
  confidence_score: number
  priority: Priority
  content_severity: ContentSeverity
  created_at: string
  assigned_to?: string
  estimated_review_minutes?: number
  precedent_count?: number
}

export interface ReviewDecision {
  decision: DecisionType
  action?: EnforcementAction
  notes?: string
}

export interface RealtimeMetrics {
  platform_safety_score: number
  cases_processed_today: number
  autonomous_resolution_rate: number
  avg_resolution_time_minutes: number
  review_queue_depth: number
  elevated_threat_level: boolean
  threat_distribution: Record<string, number>
  active_cases_by_stage: Record<string, number>
}

export interface QueueDepth {
  critical: number
  high: number
  medium: number
  low: number
}

export interface ThresholdConfig {
  violation_type: ViolationType
  autonomous_threshold: number
  investigation_trigger_threshold: number
}

export interface ConfigEntry {
  config_key: string
  value: Record<string, unknown>
  version_id: string
  is_active: boolean
  updated_by: string
  updated_at: string
}

export interface AuditLogEntry {
  log_id: string
  event_type: string
  case_id?: string
  user_id?: string
  action?: string
  violation_type?: string
  confidence_score?: number
  decision_source?: string
  reasoning?: string
  timestamp: string
}

export interface ReviewerExposure {
  reviewer_id: string
  today: {
    cases_reviewed: number
    harmful_content_exposure: number
    time_on_sensitive_cases_minutes: number
  }
  this_week: {
    cases_reviewed: number
    harmful_exposure_count: number
    time_on_sensitive_minutes: number
  }
  exposure_threshold_reached: boolean
}

export interface ComplianceReport {
  period: { start: string; end: string }
  total_cases: number
  autonomous_rate: number
  resolution_time_p50: number
  resolution_time_p90: number
  resolution_time_p99: number
  by_violation_type: Record<string, number>
  by_jurisdiction: Record<string, number>
}

export interface EnforcementResult {
  case_id: string
  action_status: string
  action?: string
  user_id?: string
  platform_result?: Record<string, unknown>
}

export interface Appeal {
  appeal_id: string
  enforcement_id: string
  user_id: string
  appeal_reason: string
  status: string
  created_at: string
}
