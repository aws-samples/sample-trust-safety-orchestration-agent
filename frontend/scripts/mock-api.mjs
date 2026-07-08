#!/usr/bin/env node
/**
 * SafetyAgent Mock API Server
 *
 * Serves all frontend endpoints with realistic, evolving demo data.
 * No AWS or backend required — just run: node scripts/mock-api.mjs
 *
 * Vite already proxies /api → localhost:3001, so start this alongside `npm run dev`.
 */

import http from 'node:http'
import crypto from 'node:crypto'

const PORT = 3001

// ---------------------------------------------------------------------------
//  Helpers
// ---------------------------------------------------------------------------

const uid = () => crypto.randomUUID().replace(/-/g, '')
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]
const rand = (min, max) => +(Math.random() * (max - min) + min).toFixed(3)
const randInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min
const ago = (minutes) => new Date(Date.now() - minutes * 60_000).toISOString()

// ---------------------------------------------------------------------------
//  Seed data
// ---------------------------------------------------------------------------

const VIOLATION_TYPES = [
  'scam', 'harassment', 'fake_profile', 'bot_farm',
  'explicit_content', 'repeat_offender', 'self_harm', 'illegal_activity',
]

const DISPLAY_NAMES = [
  'CryptoKing99', 'LovelyLisa2024', 'TravelDude42', 'SweetHeart_xo',
  'InvestorPro', 'FitnessGuru88', 'DreamDate777', 'WineAndDine',
  'AdventureSeeker', 'GymRat2025', 'BeachBum_22', 'CoffeeAddict',
  'MusicLover_23', 'BookwormBella', 'SunshineSmile', 'NightOwl_NYC',
  'QuickBuck_Pro', 'SweetTalker01', 'FakeLove99', 'MoneyMoves_X',
  'TooGoodToBeTrue', 'PuppyDad_Rex', 'WanderlustSoul', 'YogaLife_Om',
  'ChefAtHome', 'HikingHero', 'UrbanExplorer', 'RomanceScammer',
]

const ACTIONS = ['warning', 'content_removal', 'temp_suspension', 'permanent_ban', 'rate_limit']
const PRIORITIES = ['critical', 'high', 'medium', 'low']
const STATUSES = ['investigating', 'pending_review', 'in_review', 'escalated']

const SCAM_MESSAGES = [
  "Hey gorgeous! I've been making amazing returns with this new crypto platform. Want me to show you?",
  "I know we just matched but I feel such a deep connection. Can you help me with a small emergency?",
  "Check out this link — my friend made $50K last month! You should get in early.",
  "I'm deployed overseas and can't access my bank. Could you send me a gift card temporarily?",
  "I have an exclusive investment opportunity. Most people make 300% returns in the first week.",
  "You seem really smart — I bet you'd be great at trading. Let me send you my mentor's contact.",
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
//  State — evolves over time to simulate a live system
// ---------------------------------------------------------------------------

let cycleCount = 0

function buildCases() {
  const cases = []
  for (let i = 0; i < 18; i++) {
    const v = pick(VIOLATION_TYPES)
    const minutesAgo = randInt(5, 720)
    cases.push({
      case_id: `CASE-${uid().slice(0, 8).toUpperCase()}`,
      user_id: `user-${uid().slice(0, 12)}`,
      display_name: pick(DISPLAY_NAMES),
      status: pick(STATUSES),
      violation_type: v,
      confidence_score: rand(0.45, 0.98),
      content_severity: pick(['low', 'medium', 'high', 'extreme']),
      created_at: ago(minutesAgo),
      updated_at: ago(minutesAgo - randInt(1, 5)),
      audit_trail_ids: [uid().slice(0, 16), uid().slice(0, 16)],
      trigger_source: pick(['kinesis_behavioral', 'user_report', 'cross_platform']),
    })
  }
  return cases
}

function buildReviewQueue() {
  const items = []
  for (let i = 0; i < 14; i++) {
    const v = pick(VIOLATION_TYPES)
    items.push({
      queue_id: `Q-${uid().slice(0, 8).toUpperCase()}`,
      case_id: `CASE-${uid().slice(0, 8).toUpperCase()}`,
      user_id: `user-${uid().slice(0, 12)}`,
      violation_type: v,
      confidence_score: rand(0.42, 0.89),
      priority: pick(PRIORITIES),
      content_severity: pick(['low', 'medium', 'high', 'extreme']),
      created_at: ago(randInt(3, 360)),
      estimated_review_minutes: pick([5, 10, 15, 20, 30]),
      precedent_count: randInt(0, 12),
    })
  }
  return items
}

function buildAuditLog() {
  const entries = []
  const eventTypes = [
    'enforcement_executed', 'case_created', 'investigation_started',
    'confidence_calculated', 'case_escalated', 'decision_submitted',
  ]
  for (let i = 0; i < 15; i++) {
    const et = pick(eventTypes)
    entries.push({
      log_id: `AUD-${uid().slice(0, 12).toUpperCase()}`,
      event_type: et,
      case_id: `CASE-${uid().slice(0, 8).toUpperCase()}`,
      user_id: `user-${uid().slice(0, 12)}`,
      action: et === 'enforcement_executed' || et === 'decision_submitted'
        ? pick(ACTIONS)
        : undefined,
      violation_type: pick(VIOLATION_TYPES),
      confidence_score: rand(0.45, 0.97),
      decision_source: et === 'enforcement_executed' ? 'autonomous' : et === 'decision_submitted' ? 'human_reviewer' : undefined,
      timestamp: ago(randInt(1, 600)),
    })
  }
  entries.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
  return entries
}

let cases = buildCases()
let reviewQueue = buildReviewQueue()
let auditLog = buildAuditLog()

// Refresh some data periodically to simulate live pipeline
setInterval(() => {
  cycleCount++

  // Add a new case every ~10 seconds
  const v = pick(VIOLATION_TYPES)
  const newCase = {
    case_id: `CASE-${uid().slice(0, 8).toUpperCase()}`,
    user_id: `user-${uid().slice(0, 12)}`,
    display_name: pick(DISPLAY_NAMES),
    status: pick(STATUSES),
    violation_type: v,
    confidence_score: rand(0.45, 0.98),
    content_severity: pick(['low', 'medium', 'high', 'extreme']),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    audit_trail_ids: [uid().slice(0, 16)],
    trigger_source: pick(['kinesis_behavioral', 'user_report', 'cross_platform']),
  }
  cases.unshift(newCase)
  if (cases.length > 25) cases.pop()

  // Resolve oldest case every other cycle
  if (cycleCount % 2 === 0 && cases.length > 10) {
    const removed = cases.pop()
    auditLog.unshift({
      log_id: `AUD-${uid().slice(0, 12).toUpperCase()}`,
      event_type: 'enforcement_executed',
      case_id: removed.case_id,
      user_id: removed.user_id,
      action: pick(ACTIONS),
      violation_type: removed.violation_type,
      confidence_score: removed.confidence_score,
      decision_source: 'autonomous',
      timestamp: new Date().toISOString(),
    })
    if (auditLog.length > 20) auditLog.pop()
  }

  // Refresh review queue item
  if (cycleCount % 3 === 0) {
    if (reviewQueue.length > 12) reviewQueue.pop()
    reviewQueue.unshift({
      queue_id: `Q-${uid().slice(0, 8).toUpperCase()}`,
      case_id: newCase.case_id,
      user_id: newCase.user_id,
      violation_type: newCase.violation_type,
      confidence_score: rand(0.42, 0.89),
      priority: pick(PRIORITIES),
      content_severity: newCase.content_severity,
      created_at: new Date().toISOString(),
      estimated_review_minutes: pick([5, 10, 15, 20]),
      precedent_count: randInt(0, 8),
    })
  }
}, 3_000)

// ---------------------------------------------------------------------------
//  Evidence builder — generates a rich evidence package for any case
// ---------------------------------------------------------------------------

function buildEvidence(caseId, visibility) {
  const userId = `user-${uid().slice(0, 12)}`
  const violation = pick(VIOLATION_TYPES)
  const isScam = violation === 'scam'
  const isHarassment = violation === 'harassment'

  const messages = []
  const pool = isScam ? SCAM_MESSAGES : isHarassment ? HARASSMENT_MESSAGES : NORMAL_MESSAGES
  const msgCount = randInt(4, 12)
  for (let i = 0; i < msgCount; i++) {
    messages.push({
      message_id: `msg-${uid().slice(0, 10)}`,
      content: visibility === 'labels_only' ? '[Content hidden]' : pick(pool),
      sent_at: ago(randInt(1, 480)),
      recipient_id: `user-${uid().slice(0, 8)}`,
      flagged: Math.random() > 0.5,
    })
  }

  return {
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
        'Asking for money',
        'Fake photos',
        'Threatening messages',
        'Spam / bot behavior',
        'Inappropriate content',
        'Underage suspicion',
      ]),
      created_at: ago(randInt(60, 1440)),
    })),
    content_analysis: {
      scam_indicators: isScam
        ? [
            { type: 'financial_solicitation', pattern: 'crypto investment pitch', severity: 'high', context: 'Mentioned crypto returns in 3 of 6 messages' },
            { type: 'external_link', pattern: 'suspicious URL detected', severity: 'high', context: 'Link to unregistered trading platform' },
            { type: 'love_bombing', pattern: 'rapid intimacy escalation', severity: 'medium', context: 'Professed love within 24 hours of matching' },
            { type: 'urgency_pressure', pattern: 'time-limited offer language', severity: 'medium', context: '"Act now before the window closes"' },
          ]
        : [],
      threat_indicators: isHarassment
        ? [
            { type: 'threatening_language', pattern: 'implicit threat detected', severity: 'high', context: 'Referenced knowing victim\'s workplace' },
            { type: 'stalking_behavior', pattern: 'multi-account contact', severity: 'extreme', context: 'Created 3 accounts to contact same user' },
          ]
        : [],
      crisis_indicators: violation === 'self_harm'
        ? [
            { type: 'self_harm_language', pattern: 'expressions of hopelessness', severity: 'extreme', context: 'Multiple messages indicating crisis' },
          ]
        : [],
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
    cross_platform_intelligence: Math.random() > 0.4
      ? {
          match_type: pick(['device_fingerprint', 'email_hash', 'phone_hash', 'behavioral_pattern']),
          confidence: rand(0.6, 0.98),
          source_platform: pick(['Tinder', 'Match.com', 'OkCupid', 'Plenty of Fish', 'BLK']),
          ban_reason: Math.random() > 0.5
            ? pick(['Romance scam', 'Harassment', 'Fake profile', 'Underage', 'Bot network'])
            : undefined,
        }
      : undefined,
    sources_unavailable: Math.random() > 0.8 ? ['payment_history'] : [],
    assembled_at: ago(randInt(1, 30)),
  }
}

// ---------------------------------------------------------------------------
//  Metrics — drifts slightly each request to look alive
// ---------------------------------------------------------------------------

let baseSafetyScore = 82
let baseCasesProcessed = 1247
let baseQueueDepth = 23

function getMetrics() {
  baseSafetyScore = Math.max(60, Math.min(95, baseSafetyScore + randInt(-2, 2)))
  baseCasesProcessed += randInt(1, 8)
  baseQueueDepth = Math.max(5, Math.min(60, baseQueueDepth + randInt(-3, 3)))

  return {
    platform_safety_score: baseSafetyScore,
    cases_processed_today: baseCasesProcessed,
    autonomous_resolution_rate: rand(0.71, 0.79),
    avg_resolution_time_minutes: rand(7.2, 12.8),
    review_queue_depth: baseQueueDepth,
    elevated_threat_level: baseSafetyScore < 70,
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

// ---------------------------------------------------------------------------
//  Config
// ---------------------------------------------------------------------------

const configs = [
  { config_key: 'threshold_scam', value: { violation_type: 'scam', autonomous_threshold: 0.90, investigation_trigger_threshold: 0.50 }, version_id: 'v-001', is_active: true, updated_by: 'admin@example.com', updated_at: ago(1440) },
  { config_key: 'threshold_harassment', value: { violation_type: 'harassment', autonomous_threshold: 0.85, investigation_trigger_threshold: 0.45 }, version_id: 'v-002', is_active: true, updated_by: 'admin@example.com', updated_at: ago(1440) },
  { config_key: 'threshold_fake_profile', value: { violation_type: 'fake_profile', autonomous_threshold: 0.88, investigation_trigger_threshold: 0.50 }, version_id: 'v-003', is_active: true, updated_by: 'admin@example.com', updated_at: ago(2880) },
  { config_key: 'threshold_bot_farm', value: { violation_type: 'bot_farm', autonomous_threshold: 0.85, investigation_trigger_threshold: 0.55 }, version_id: 'v-004', is_active: true, updated_by: 'admin@example.com', updated_at: ago(2880) },
  { config_key: 'threshold_self_harm', value: { violation_type: 'self_harm', autonomous_threshold: 1.00, investigation_trigger_threshold: 0.30 }, version_id: 'v-005', is_active: true, updated_by: 'admin@example.com', updated_at: ago(4320) },
  { config_key: 'threshold_child_safety', value: { violation_type: 'child_safety', autonomous_threshold: 1.00, investigation_trigger_threshold: 0.25 }, version_id: 'v-006', is_active: true, updated_by: 'admin@example.com', updated_at: ago(4320) },
  { config_key: 'threshold_illegal_activity', value: { violation_type: 'illegal_activity', autonomous_threshold: 1.00, investigation_trigger_threshold: 0.35 }, version_id: 'v-007', is_active: true, updated_by: 'admin@example.com', updated_at: ago(4320) },
  { config_key: 'threshold_repeat_offender', value: { violation_type: 'repeat_offender', autonomous_threshold: 0.80, investigation_trigger_threshold: 0.40 }, version_id: 'v-008', is_active: true, updated_by: 'admin@example.com', updated_at: ago(1440) },
]

// ---------------------------------------------------------------------------
//  Reviewer exposure
// ---------------------------------------------------------------------------

function getExposure(reviewerId) {
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

// ---------------------------------------------------------------------------
//  Router
// ---------------------------------------------------------------------------

function route(method, url, body) {
  // Auth
  if (method === 'POST' && url === '/api/v1/auth/login') {
    const { email, password } = body || {}
    if (email === 'admin@example.com' && password === 'demo-password') {
      return {
        token: `demo-jwt-${uid().slice(0, 24)}`,
        user_id: 'usr-admin-001',
        email,
        role: 'admin',
      }
    }
    // Accept any credentials for demo flexibility
    return {
      token: `demo-jwt-${uid().slice(0, 24)}`,
      user_id: `usr-${uid().slice(0, 8)}`,
      email: email || 'demo@example.com',
      role: 'admin',
    }
  }

  // Metrics
  if (method === 'GET' && url === '/api/v1/metrics/realtime') {
    return getMetrics()
  }

  // Recent actions
  if (method === 'GET' && url === '/api/v1/actions/recent') {
    return { recent_actions: auditLog }
  }

  // Active cases
  if (method === 'GET' && url === '/api/v1/cases/active') {
    return { cases }
  }

  // Evidence
  if (method === 'GET' && url.startsWith('/api/v1/cases/') && url.includes('/evidence')) {
    const parts = url.split('/')
    const caseId = parts[4]
    const params = new URL(`http://x${url}`).searchParams
    const visibility = params.get('visibility') || 'labels_only'
    return { case_id: caseId, evidence: buildEvidence(caseId, visibility) }
  }

  // Decision
  if (method === 'POST' && url.match(/\/api\/v1\/cases\/[^/]+\/decision/)) {
    const parts = url.split('/')
    const caseId = parts[4]
    return {
      case_id: caseId,
      action_status: 'executed',
      action: body?.action || 'warning',
      user_id: `user-${uid().slice(0, 12)}`,
    }
  }

  // Review queue
  if (method === 'GET' && url.startsWith('/api/v1/review-queue')) {
    const params = new URL(`http://x${url}`).searchParams
    const priority = params.get('priority')
    let filtered = reviewQueue
    if (priority) {
      filtered = reviewQueue.filter((r) => r.priority === priority)
    }
    return {
      cases: filtered,
      total_count: filtered.length,
      queue_depth_by_priority: {
        critical: reviewQueue.filter((r) => r.priority === 'critical').length,
        high: reviewQueue.filter((r) => r.priority === 'high').length,
        medium: reviewQueue.filter((r) => r.priority === 'medium').length,
        low: reviewQueue.filter((r) => r.priority === 'low').length,
      },
    }
  }

  // Config
  if (method === 'GET' && url === '/api/v1/config/current') {
    const configsMap = {}
    for (const c of configs) {
      configsMap[c.config_key] = JSON.stringify(c.value)
    }
    return { configs: configsMap }
  }

  if (method === 'PUT' && url === '/api/v1/config/thresholds') {
    const newVersion = `v-${uid().slice(0, 6)}`
    return { config_key: `threshold_${body?.violation_type}`, version_id: newVersion, status: 'active' }
  }

  if (method === 'POST' && url === '/api/v1/config/rollback') {
    return { config_key: body?.config_key, new_version_id: `v-${uid().slice(0, 6)}`, status: 'rolled_back' }
  }

  // Reviewer exposure
  if (method === 'GET' && url.match(/\/api\/v1\/reviewers\/[^/]+\/exposure-metrics/)) {
    const parts = url.split('/')
    const reviewerId = parts[4]
    return getExposure(reviewerId)
  }

  // Audit export
  if (method === 'GET' && url.startsWith('/api/v1/audit/export')) {
    return { download_url: 'https://example.com/demo-audit-export.json' }
  }

  // Compliance report
  if (method === 'GET' && url.startsWith('/api/v1/reports/compliance')) {
    return {
      period: { start: '2026-04-01', end: '2026-04-30' },
      total_cases: randInt(3000, 5000),
      autonomous_rate: rand(0.72, 0.78),
      resolution_time_p50: rand(5.0, 8.0),
      resolution_time_p90: rand(10.0, 14.0),
      resolution_time_p99: rand(28.0, 45.0),
      by_violation_type: {
        scam: randInt(800, 1400),
        harassment: randInt(400, 800),
        fake_profile: randInt(500, 900),
        bot_farm: randInt(100, 300),
        self_harm: randInt(30, 80),
      },
      by_jurisdiction: {
        US: randInt(1500, 2500),
        UK: randInt(300, 600),
        EU: randInt(400, 800),
        APAC: randInt(200, 500),
      },
    }
  }

  // Health check
  if (method === 'GET' && (url === '/api/v1/health' || url === '/health')) {
    return { status: 'healthy', version: '1.0.0-demo' }
  }

  return null
}

// ---------------------------------------------------------------------------
//  Server
// ---------------------------------------------------------------------------

const server = http.createServer((req, res) => {
  // CORS for direct access (non-proxy)
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    res.writeHead(204)
    res.end()
    return
  }

  let body = ''
  req.on('data', (chunk) => { body += chunk })
  req.on('end', () => {
    const parsed = body ? JSON.parse(body) : undefined
    const result = route(req.method, req.url, parsed)

    if (result === null) {
      res.writeHead(404, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: 'Not found' }))
      return
    }

    const ts = new Date().toLocaleTimeString()
    console.log(`  [${ts}] ${req.method} ${req.url} → 200`)

    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify(result))
  })
})

server.listen(PORT, () => {
  console.log()
  console.log('  ╔══════════════════════════════════════════════╗')
  console.log('  ║   SafetyAgent Mock API Server                ║')
  console.log(`  ║   http://localhost:${PORT}/api/v1              ║`)
  console.log('  ║                                              ║')
  console.log('  ║   Login: admin@example.com           ║')
  console.log('  ║   Pass:  demo-password                     ║')
  console.log('  ║                                              ║')
  console.log('  ║   Data refreshes every 10s to simulate       ║')
  console.log('  ║   a live pipeline. Press Ctrl+C to stop.     ║')
  console.log('  ╚══════════════════════════════════════════════╝')
  console.log()
})
