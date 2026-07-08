import type {
  Case,
  EvidencePackage,
  ReviewQueueItem,
  RealtimeMetrics,
  AuditLogEntry,
  QueueDepth,
  ReviewerExposure,
  EnforcementResult,
} from '@/types'
import { CaseStatus, ViolationType, Priority, ContentSeverity } from '@/types'

const pick = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)]
const rand = (min: number, max: number) => +(Math.random() * (max - min) + min).toFixed(3)
const randInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min
const ago = (minutes: number) => new Date(Date.now() - minutes * 60_000).toISOString()
const uid = () => Math.random().toString(36).slice(2, 14)

const DISPLAY_NAMES = [
  'CryptoKing99', 'LovelyLisa2024', 'TravelDude42', 'SweetHeart_xo',
  'InvestorPro', 'FitnessGuru88', 'DreamDate777', 'WineAndDine',
  'AdventureSeeker', 'GymRat2025', 'BeachBum_22', 'CoffeeAddict',
  'MusicLover_23', 'BookwormBella', 'SunshineSmile', 'NightOwl_NYC',
  'QuickBuck_Pro', 'SweetTalker01', 'FakeLove99', 'MoneyMoves_X',
  'TooGoodToBeTrue', 'PuppyDad_Rex', 'WanderlustSoul', 'YogaLife_Om',
  'ChefAtHome', 'HikingHero', 'UrbanExplorer', 'RomanceScammer',
]

const VIOLATION_TYPES: ViolationType[] = [
  ViolationType.Scam, ViolationType.Harassment, ViolationType.FakeProfile,
  ViolationType.BotFarm, ViolationType.RepeatOffender, ViolationType.SelfHarm,
  ViolationType.IllegalActivity,
]

const ACTIONS = ['warning', 'content_removal', 'temp_suspension', 'permanent_ban', 'rate_limit']

const SCAM_MESSAGES = [
  "Hey gorgeous! I've been making amazing returns with this new crypto platform.",
  "I know we just matched but I feel such a deep connection. Can you help me with a small emergency?",
  "Check out this link — my friend made $50K last month! You should get in early.",
  "I'm deployed overseas and can't access my bank. Could you send me a gift card?",
  "I have an exclusive investment opportunity. Most people make 300% returns in the first week.",
  "You seem really smart — let me send you my mentor's contact for trading.",
]

const HARASSMENT_MESSAGES = [
  "Why won't you answer me? I've sent you 15 messages.",
  "I saw you were online. Don't ignore me.",
  "You'll regret unmatching me. I know where you work.",
  "Created this new account just to talk to you again.",
]

const NORMAL_MESSAGES = [
  "Hey! I noticed you like hiking too. Any favorite trails?",
  "That photo of your dog is adorable! What breed?",
  "Would you want to grab coffee this weekend?",
  "I love that restaurant! Have you tried their brunch menu?",
]

// ---------------------------------------------------------------------------
//  Seeded data that drifts over time
// ---------------------------------------------------------------------------

let _safetyScore = 82
let _casesProcessed = 1247
let _queueDepth = 23
let _cycleCount = 0

function buildCases(): Case[] {
  const cases: Case[] = []
  for (let i = 0; i < 18; i++) {
    const minutesAgo = randInt(5, 720)
    cases.push({
      case_id: `CASE-${uid().slice(0, 8).toUpperCase()}`,
      user_id: `user-${uid()}`,
      status: pick([CaseStatus.Investigating, CaseStatus.PendingReview, CaseStatus.InReview, CaseStatus.Escalated]),
      violation_type: pick(VIOLATION_TYPES),
      confidence_score: rand(0.45, 0.98),
      content_severity: pick([ContentSeverity.Low, ContentSeverity.Medium, ContentSeverity.High, ContentSeverity.Extreme]),
      created_at: ago(minutesAgo),
      updated_at: ago(minutesAgo - randInt(1, 5)),
      audit_trail_ids: [uid(), uid()],
      trigger_source: pick(['kinesis_behavioral', 'user_report', 'cross_platform']),
    })
  }
  return cases
}

function buildReviewQueue(): ReviewQueueItem[] {
  const items: ReviewQueueItem[] = []
  for (let i = 0; i < 14; i++) {
    items.push({
      queue_id: `Q-${uid().slice(0, 8).toUpperCase()}`,
      case_id: `CASE-${uid().slice(0, 8).toUpperCase()}`,
      user_id: `user-${uid()}`,
      violation_type: pick(VIOLATION_TYPES),
      confidence_score: rand(0.42, 0.89),
      priority: pick([Priority.Critical, Priority.High, Priority.Medium, Priority.Low]),
      content_severity: pick([ContentSeverity.Low, ContentSeverity.Medium, ContentSeverity.High, ContentSeverity.Extreme]),
      created_at: ago(randInt(3, 360)),
      estimated_review_minutes: pick([5, 10, 15, 20, 30]),
      precedent_count: randInt(0, 12),
    })
  }
  return items
}

function buildAuditLog(): AuditLogEntry[] {
  const entries: AuditLogEntry[] = []
  const eventTypes = [
    'enforcement_executed', 'case_created', 'investigation_started',
    'confidence_calculated', 'case_escalated', 'decision_submitted',
  ]
  for (let i = 0; i < 15; i++) {
    const et = pick(eventTypes)
    entries.push({
      log_id: `AUD-${uid().toUpperCase()}`,
      event_type: et,
      case_id: `CASE-${uid().slice(0, 8).toUpperCase()}`,
      user_id: `user-${uid()}`,
      action: (et === 'enforcement_executed' || et === 'decision_submitted') ? pick(ACTIONS) : undefined,
      violation_type: pick(VIOLATION_TYPES),
      confidence_score: rand(0.45, 0.97),
      decision_source: et === 'enforcement_executed' ? 'autonomous' : et === 'decision_submitted' ? 'human_reviewer' : undefined,
      timestamp: ago(randInt(1, 600)),
    })
  }
  entries.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  return entries
}

let _cases = buildCases()
let _reviewQueue = buildReviewQueue()
let _auditLog = buildAuditLog()

function evolve() {
  _cycleCount++

  const v = pick(VIOLATION_TYPES)
  const newCase: Case = {
    case_id: `CASE-${uid().slice(0, 8).toUpperCase()}`,
    user_id: `user-${uid()}`,
    status: pick([CaseStatus.Investigating, CaseStatus.PendingReview, CaseStatus.InReview]),
    violation_type: v,
    confidence_score: rand(0.45, 0.98),
    content_severity: pick([ContentSeverity.Low, ContentSeverity.Medium, ContentSeverity.High, ContentSeverity.Extreme]),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    audit_trail_ids: [uid()],
    trigger_source: pick(['kinesis_behavioral', 'user_report', 'cross_platform']),
  }
  _cases.unshift(newCase)
  if (_cases.length > 25) _cases.pop()

  if (_cycleCount % 2 === 0 && _cases.length > 10) {
    const removed = _cases.pop()!
    _auditLog.unshift({
      log_id: `AUD-${uid().toUpperCase()}`,
      event_type: 'enforcement_executed',
      case_id: removed.case_id,
      user_id: removed.user_id,
      action: pick(ACTIONS),
      violation_type: removed.violation_type,
      confidence_score: removed.confidence_score,
      decision_source: 'autonomous',
      timestamp: new Date().toISOString(),
    })
    if (_auditLog.length > 20) _auditLog.pop()
  }

  if (_cycleCount % 3 === 0) {
    if (_reviewQueue.length > 12) _reviewQueue.pop()
    _reviewQueue.unshift({
      queue_id: `Q-${uid().slice(0, 8).toUpperCase()}`,
      case_id: newCase.case_id,
      user_id: newCase.user_id,
      violation_type: newCase.violation_type,
      confidence_score: rand(0.42, 0.89),
      priority: pick([Priority.Critical, Priority.High, Priority.Medium, Priority.Low]),
      content_severity: newCase.content_severity,
      created_at: new Date().toISOString(),
      estimated_review_minutes: pick([5, 10, 15, 20]),
      precedent_count: randInt(0, 8),
    })
  }
}

setInterval(evolve, 10_000)

// ---------------------------------------------------------------------------
//  Mock route handlers
// ---------------------------------------------------------------------------

export function mockLogin(_email: string, _password: string) {
  return {
    token: `demo-jwt-${uid()}`,
    user_id: 'usr-admin-001',
    email: _email || 'admin@safetyagent.example.com',
    role: 'admin',
  }
}

export function mockMetrics(): RealtimeMetrics {
  _safetyScore = Math.max(60, Math.min(95, _safetyScore + randInt(-2, 2)))
  _casesProcessed += randInt(1, 8)
  _queueDepth = Math.max(5, Math.min(60, _queueDepth + randInt(-3, 3)))

  return {
    platform_safety_score: _safetyScore,
    cases_processed_today: _casesProcessed,
    autonomous_resolution_rate: rand(0.71, 0.79),
    avg_resolution_time_minutes: rand(7.2, 12.8),
    review_queue_depth: _queueDepth,
    elevated_threat_level: _safetyScore < 70,
    threat_distribution: {
      scam: randInt(80, 160),
      harassment: randInt(40, 90),
      fake_profile: randInt(50, 100),
      bot_farm: randInt(15, 40),
      explicit_content: randInt(20, 55),
      repeat_offender: randInt(10, 30),
      self_harm: randInt(3, 12),
    },
    active_cases_by_stage: {
      investigating: randInt(8, 20),
      pending_review: randInt(5, 15),
      in_review: randInt(3, 10),
      escalated: randInt(2, 8),
    },
  }
}

export function mockRecentActions(): { recent_actions: AuditLogEntry[] } {
  return { recent_actions: _auditLog }
}

export function mockActiveCases(): { cases: Case[] } {
  return { cases: _cases }
}

export function mockEvidence(caseId: string, visibility: string): { case_id: string; evidence: EvidencePackage } {
  const userId = `user-${uid()}`
  const violation = pick(VIOLATION_TYPES)
  const isScam = violation === ViolationType.Scam
  const isHarassment = violation === ViolationType.Harassment

  const pool = isScam ? SCAM_MESSAGES : isHarassment ? HARASSMENT_MESSAGES : NORMAL_MESSAGES
  const messages = Array.from({ length: randInt(4, 12) }, () => ({
    message_id: `msg-${uid().slice(0, 10)}`,
    content: visibility === 'labels_only' ? '[Content hidden]' : pick(pool),
    sent_at: ago(randInt(1, 480)),
    recipient_id: `user-${uid().slice(0, 8)}`,
    flagged: Math.random() > 0.5,
  }))

  const evidence: EvidencePackage = {
    case_id: caseId,
    user_id: userId,
    profile_metadata: {
      user_id: userId,
      display_name: pick(DISPLAY_NAMES),
      account_age_days: randInt(0, 365),
      profile_completeness: rand(0.3, 1.0),
      photo_count: randInt(1, 8),
      verification_status: pick(['verified', 'unverified', 'pending']),
    },
    message_history: {
      messages,
      total_count: messages.length + randInt(0, 30),
    },
    previous_reports: Array.from({ length: randInt(0, 4) }, () => ({
      report_id: `RPT-${uid().slice(0, 8)}`,
      reporter_id: `user-${uid().slice(0, 8)}`,
      reason: pick([
        'Asking for money', 'Fake photos', 'Threatening messages',
        'Spam / bot behavior', 'Inappropriate content', 'Underage suspicion',
      ]),
      created_at: ago(randInt(60, 1440)),
    })),
    content_analysis: {
      scam_indicators: isScam ? [
        { type: 'financial_solicitation', pattern: 'crypto investment pitch', severity: 'high', context: 'Mentioned crypto returns in 3 of 6 messages' },
        { type: 'external_link', pattern: 'suspicious URL detected', severity: 'high', context: 'Link to unregistered trading platform' },
        { type: 'love_bombing', pattern: 'rapid intimacy escalation', severity: 'medium', context: 'Professed love within 24 hours of matching' },
        { type: 'urgency_pressure', pattern: 'time-limited offer language', severity: 'medium', context: '"Act now before the window closes"' },
      ] : [],
      threat_indicators: isHarassment ? [
        { type: 'threatening_language', pattern: 'implicit threat detected', severity: 'high', context: "Referenced knowing victim's workplace" },
        { type: 'stalking_behavior', pattern: 'multi-account contact', severity: 'extreme', context: 'Created 3 accounts to contact same user' },
      ] : [],
      crisis_indicators: violation === ViolationType.SelfHarm ? [
        { type: 'self_harm_language', pattern: 'expressions of hopelessness', severity: 'extreme', context: 'Multiple messages indicating crisis' },
      ] : [],
      sentiment: {
        overall: pick(['negative', 'hostile', 'manipulative', 'neutral']),
        manipulation_score: isScam ? rand(0.7, 0.95) : rand(0.05, 0.4),
        aggression_score: isHarassment ? rand(0.65, 0.92) : rand(0.02, 0.3),
      },
    },
    image_analysis: {
      profile_images: Array.from({ length: randInt(1, 5) }, () => ({
        image_id: `img-${uid().slice(0, 8)}`,
        is_ai_generated: Math.random() > 0.7,
        is_stock_photo: Math.random() > 0.75,
        reverse_search_matches: randInt(0, 8),
      })),
    },
    cross_platform_intelligence: Math.random() > 0.4 ? {
      match_type: pick(['device_fingerprint', 'email_hash', 'phone_hash', 'behavioral_pattern']),
      confidence: rand(0.6, 0.98),
      source_platform: pick(['Partner A', 'Partner B', 'Partner C', 'Partner D', 'Partner E']),
      ban_reason: Math.random() > 0.5 ? pick(['Romance scam', 'Harassment', 'Fake profile', 'Underage', 'Bot network']) : undefined,
    } : undefined,
    sources_unavailable: Math.random() > 0.8 ? ['payment_history'] : [],
    assembled_at: ago(randInt(1, 30)),
  }

  return { case_id: caseId, evidence }
}

export function mockReviewQueue(priority?: string): { cases: ReviewQueueItem[]; total_count: number; queue_depth_by_priority: QueueDepth } {
  const filtered = priority ? _reviewQueue.filter((r) => r.priority === priority) : _reviewQueue
  return {
    cases: filtered,
    total_count: filtered.length,
    queue_depth_by_priority: {
      critical: _reviewQueue.filter((r) => r.priority === Priority.Critical).length,
      high: _reviewQueue.filter((r) => r.priority === Priority.High).length,
      medium: _reviewQueue.filter((r) => r.priority === Priority.Medium).length,
      low: _reviewQueue.filter((r) => r.priority === Priority.Low).length,
    },
  }
}

export function mockDecision(caseId: string, action?: string): EnforcementResult {
  return {
    case_id: caseId,
    action_status: 'executed',
    action: action || 'warning',
    user_id: `user-${uid()}`,
  }
}

export function mockConfigs(): { configs: Record<string, string> } {
  return {
    configs: {
      threshold_scam: JSON.stringify({ violation_type: 'scam', autonomous_threshold: 0.90, investigation_trigger_threshold: 0.50 }),
      threshold_harassment: JSON.stringify({ violation_type: 'harassment', autonomous_threshold: 0.85, investigation_trigger_threshold: 0.45 }),
      threshold_fake_profile: JSON.stringify({ violation_type: 'fake_profile', autonomous_threshold: 0.88, investigation_trigger_threshold: 0.50 }),
      threshold_bot_farm: JSON.stringify({ violation_type: 'bot_farm', autonomous_threshold: 0.85, investigation_trigger_threshold: 0.55 }),
      threshold_self_harm: JSON.stringify({ violation_type: 'self_harm', autonomous_threshold: 1.00, investigation_trigger_threshold: 0.30 }),
      threshold_child_safety: JSON.stringify({ violation_type: 'child_safety', autonomous_threshold: 1.00, investigation_trigger_threshold: 0.25 }),
      threshold_illegal_activity: JSON.stringify({ violation_type: 'illegal_activity', autonomous_threshold: 1.00, investigation_trigger_threshold: 0.35 }),
      threshold_repeat_offender: JSON.stringify({ violation_type: 'repeat_offender', autonomous_threshold: 0.80, investigation_trigger_threshold: 0.40 }),
    },
  }
}

export function mockExposure(reviewerId: string): ReviewerExposure {
  return {
    reviewer_id: reviewerId,
    today: {
      cases_reviewed: randInt(8, 18),
      harmful_content_exposure: randInt(3, 14),
      time_on_sensitive_cases_minutes: randInt(20, 90),
    },
    this_week: {
      cases_reviewed: randInt(50, 120),
      harmful_exposure_count: randInt(15, 55),
      time_on_sensitive_minutes: randInt(120, 400),
    },
    exposure_threshold_reached: Math.random() > 0.7,
  }
}

export function mockConfigUpdate(violationType?: string): { config_key: string; version_id: string; status: string } {
  return { config_key: `threshold_${violationType}`, version_id: `v-${uid().slice(0, 6)}`, status: 'active' }
}

export function mockConfigRollback(configKey?: string): { config_key: string; new_version_id: string; status: string } {
  return { config_key: configKey || 'unknown', new_version_id: `v-${uid().slice(0, 6)}`, status: 'rolled_back' }
}

export function mockAuditExport(): { download_url: string } {
  return { download_url: '#demo-export' }
}

// ---------------------------------------------------------------------------
//  Route resolver — matches path patterns and returns mock data
// ---------------------------------------------------------------------------

export function resolveMock(method: string, path: string, body?: unknown): unknown | null {
  if (method === 'GET' && path === '/metrics/realtime') return mockMetrics()
  if (method === 'GET' && path === '/actions/recent') return mockRecentActions()
  if (method === 'GET' && path === '/cases/active') return mockActiveCases()

  if (method === 'GET' && path.startsWith('/cases/') && path.includes('/evidence')) {
    const caseId = path.split('/')[2]
    const params = new URLSearchParams(path.split('?')[1] || '')
    return mockEvidence(caseId, params.get('visibility') || 'labels_only')
  }

  if (method === 'POST' && /^\/cases\/[^/]+\/decision/.test(path)) {
    const caseId = path.split('/')[2]
    const b = body as Record<string, string> | undefined
    return mockDecision(caseId, b?.action)
  }

  if (method === 'GET' && path.startsWith('/review-queue')) {
    const params = new URLSearchParams(path.split('?')[1] || '')
    return mockReviewQueue(params.get('priority') || undefined)
  }

  if (method === 'GET' && path === '/config/current') return mockConfigs()
  if (method === 'PUT' && path === '/config/thresholds') {
    const b = body as Record<string, string> | undefined
    return mockConfigUpdate(b?.violation_type)
  }
  if (method === 'POST' && path === '/config/rollback') {
    const b = body as Record<string, string> | undefined
    return mockConfigRollback(b?.config_key)
  }

  if (method === 'GET' && /^\/reviewers\/[^/]+\/exposure-metrics/.test(path)) {
    const reviewerId = path.split('/')[2]
    return mockExposure(reviewerId)
  }

  if (method === 'GET' && path.startsWith('/audit/export')) return mockAuditExport()

  return null
}
