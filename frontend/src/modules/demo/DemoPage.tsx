import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface StepDef {
  title: string
  narrative: string
}

/* ------------------------------------------------------------------ */
/*  Step definitions                                                   */
/* ------------------------------------------------------------------ */

const STEPS: StepDef[] = [
  {
    title: 'SafetyAgent Live Demo',
    narrative:
      "Watch SafetyAgent's autonomous safety pipeline process a real threat scenario — from initial detection through investigation, decision, and enforcement. This demo follows a crypto-romance scam that targets multiple users across the platform.",
  },
  {
    title: 'Behavioral Anomaly Detected',
    narrative:
      "User ‘CryptoKing99’ created their account 2 days ago and has already messaged 47 users. Their message velocity is 8.2x above normal. The behavioral event processor scores them at 0.87 anomaly — well above the 0.5 investigation threshold.",
  },
  {
    title: 'Evidence Assembly (Parallel)',
    narrative:
      'Step Functions launches 5 parallel evidence gathering tasks. In under 45 seconds, the system assembles: message content analysis (Bedrock Claude identifies crypto investment scam patterns), image analysis (stock photo detected via reverse search), cross-platform check (device fingerprint matches a banned user on a partner app), and previous reports from 3 other users.',
  },
  {
    title: 'Confidence: 94.2% — Scam',
    narrative:
      'The confidence calculator weighs multiple signals: 4 scam patterns detected (+0.25 each), stock photo match (+0.15), cross-platform bad actor match (+0.20), 3 previous reports (+0.09 boost). Final score: 94.2% scam confidence — above the 90% threshold for autonomous permanent ban.',
  },
  {
    title: 'Autonomous Action Approved',
    narrative:
      'The policy engine evaluates: scam at 94.2% exceeds the 90% permanent ban threshold. This is NOT a sensitive category (not self-harm, child safety, or illegal activity), so autonomous enforcement is approved. No human review needed for this clear-cut case.',
  },
  {
    title: 'Account Permanently Banned',
    narrative:
      'Within 12 minutes of first detection: account permanently banned, all active conversations terminated, device fingerprint + email hash added to cross-platform blocklist (shared with partner apps), appeal record created, user notified. Full audit trail logged immutably.',
  },
  {
    title: 'Sensitive Case: Always Human',
    narrative:
      "Not all cases are this clear-cut. When SafetyAgent detects self-harm indicators, it NEVER takes autonomous action. Instead: wellbeing resources are sent to the user within 5 minutes, the case is immediately escalated to a trained human reviewer with full context, and the system blocks any automated enforcement to protect the vulnerable user.",
  },
]

/* ------------------------------------------------------------------ */
/*  Progress bar                                                       */
/* ------------------------------------------------------------------ */

function ProgressBar({
  current,
  total,
  onSelect,
}: {
  current: number
  total: number
  onSelect: (i: number) => void
}) {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: total }).map((_, i) => {
        const done = i <= current
        return (
          <button
            key={i}
            onClick={() => onSelect(i)}
            aria-label={`Go to step ${i}`}
            className="group flex flex-1 flex-col items-center gap-1.5"
          >
            <div
              className={`h-1.5 w-full rounded-full transition-colors duration-300 ${
                done ? 'bg-midnight' : 'bg-gray-300 group-hover:bg-midnight/30'
              }`}
            />
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold transition-all duration-300 ${
                i === current
                  ? 'bg-midnight text-white shadow-md shadow-midnight/30'
                  : done
                    ? 'bg-midnight/20 text-midnight'
                    : 'bg-gray-200 text-gray-500 group-hover:bg-gray-300'
              }`}
            >
              {i}
            </span>
          </button>
        )
      })}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Step 0 - Pipeline diagram                                          */
/* ------------------------------------------------------------------ */

const PIPELINE_STAGES = ['Detection', 'Investigation', 'Decision', 'Enforcement']

function PipelineDiagram() {
  const [active, setActive] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setActive((p) => (p + 1) % PIPELINE_STAGES.length), 1200)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="flex items-center justify-center gap-2">
      {PIPELINE_STAGES.map((stage, i) => (
        <div key={stage} className="flex items-center gap-2">
          <div
            className={`rounded-lg px-4 py-3 text-center text-sm font-semibold transition-all duration-500 ${
              i === active
                ? 'scale-105 bg-midnight text-white shadow-lg shadow-midnight/30'
                : i < active
                  ? 'bg-midnight/20 text-midnight'
                  : 'bg-gray-100 text-gray-500'
            }`}
          >
            {stage}
          </div>
          {i < PIPELINE_STAGES.length - 1 && (
            <svg
              className={`h-5 w-5 flex-shrink-0 transition-colors duration-500 ${
                i < active ? 'text-midnight' : 'text-gray-300'
              }`}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          )}
        </div>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Step 1 - Anomaly card                                              */
/* ------------------------------------------------------------------ */

const ANOMALY_DATA = [
  { label: 'Message Velocity', value: '8.2x', note: 'above normal' },
  { label: 'Response Rate', value: '0.03', note: '3% of recipients reply' },
  { label: 'Account Age', value: '2 days', note: 'new account' },
  { label: 'Reports', value: '3', note: 'from unique users' },
  { label: 'Anomaly Score', value: '0.87', note: 'threshold: 0.50', highlight: true },
]

function AnomalyCard() {
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center gap-3 border-b border-gray-100 px-5 py-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-600">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
            />
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-900">CryptoKing99</p>
          <p className="text-xs text-gray-500">User ID: usr_8f3a...c12d &middot; Joined 2 days ago</p>
        </div>
      </div>
      <div className="space-y-3 px-5 py-4">
        {ANOMALY_DATA.map((d) => (
          <div key={d.label} className="flex items-center justify-between">
            <span className="text-sm text-gray-600">{d.label}</span>
            <div className="flex items-center gap-2">
              <span
                className={`text-sm font-semibold ${
                  d.highlight ? 'text-red-600' : 'text-gray-900'
                }`}
              >
                {d.value}
              </span>
              <span className="text-xs text-gray-400">{d.note}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Step 2 - Evidence cards                                            */
/* ------------------------------------------------------------------ */

const EVIDENCE_ITEMS = [
  {
    name: 'Message Content Analysis',
    status: 'Crypto investment scam patterns (4 matches)',
    icon: 'M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.282 48.282 0 0 0 5.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z',
  },
  {
    name: 'Image Analysis',
    status: 'Stock photo detected (reverse search match)',
    icon: 'M2.25 15.75l5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z',
  },
  {
    name: 'Cross-Platform Check',
    status: 'Device fingerprint matches a banned user on a partner platform',
    icon: 'M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418',
  },
  {
    name: 'User Reports',
    status: '3 reports: "asked me to invest in crypto"',
    icon: 'M3 3v1.5M3 21v-6m0 0 2.77-.693a9 9 0 0 1 6.208.682l.108.054a9 9 0 0 0 6.086.71l3.114-.732a48.524 48.524 0 0 1-.005-10.499l-3.11.732a9 9 0 0 1-6.085-.711l-.108-.054a9 9 0 0 0-6.208-.682L3 4.5M3 15V4.5',
  },
  {
    name: 'Behavioral Pattern',
    status: 'Rapid-fire messaging to female users aged 25-35',
    icon: 'M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605',
  },
]

function EvidencePanel() {
  const [loaded, setLoaded] = useState<boolean[]>(new Array(EVIDENCE_ITEMS.length).fill(false))

  useEffect(() => {
    const timers = EVIDENCE_ITEMS.map((_, i) =>
      setTimeout(() => setLoaded((prev) => {
        const next = [...prev]
        next[i] = true
        return next
      }), 400 + i * 600),
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="space-y-3">
      {EVIDENCE_ITEMS.map((item, i) => (
        <div
          key={item.name}
          className={`flex items-start gap-3 rounded-lg border px-4 py-3 transition-all duration-500 ${
            loaded[i]
              ? 'border-green-200 bg-green-50'
              : 'border-gray-200 bg-gray-50'
          }`}
        >
          <div
            className={`mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full transition-colors duration-500 ${
              loaded[i] ? 'bg-green-200 text-green-700' : 'bg-gray-200 text-gray-400'
            }`}
          >
            {loaded[i] ? (
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
            ) : (
              <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Z" />
              </svg>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-gray-900">{item.name}</p>
            <p
              className={`mt-0.5 text-xs transition-opacity duration-500 ${
                loaded[i] ? 'text-green-700 opacity-100' : 'text-gray-400 opacity-0'
              }`}
            >
              {item.status}
            </p>
          </div>
        </div>
      ))}
      <p className="text-center text-xs text-gray-400">Evidence assembled in 43 seconds</p>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Step 3 - Confidence meter                                          */
/* ------------------------------------------------------------------ */

const CONFIDENCE_FACTORS = [
  { label: 'Scam patterns detected (4)', value: '+0.25 each', total: '+1.00' },
  { label: 'Stock photo match', value: '', total: '+0.15' },
  { label: 'Cross-platform bad actor', value: '', total: '+0.20' },
  { label: '3 previous reports', value: '', total: '+0.09' },
]

function ConfidenceMeter() {
  const [fill, setFill] = useState(0)

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      setTimeout(() => setFill(94.2), 100)
    })
    return () => cancelAnimationFrame(id)
  }, [])

  return (
    <div className="space-y-5">
      {/* Meter */}
      <div>
        <div className="mb-2 flex items-end justify-between">
          <span className="text-sm font-medium text-gray-700">Confidence Score</span>
          <span className="text-2xl font-bold text-red-600">{fill > 0 ? '94.2%' : '0%'}</span>
        </div>
        <div className="h-5 w-full overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full rounded-full bg-gradient-to-r from-lilac to-red-500 transition-all duration-[1500ms] ease-out"
            style={{ width: `${fill}%` }}
          />
        </div>
        <div className="mt-1 flex justify-between text-xs text-gray-400">
          <span>0%</span>
          <span className="text-yellow-500">75% temp restrict</span>
          <span className="text-red-500">90% perm ban</span>
          <span>100%</span>
        </div>
      </div>

      {/* Factor breakdown */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="border-b border-gray-100 px-4 py-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Contributing Factors
          </p>
        </div>
        <div className="divide-y divide-gray-50">
          {CONFIDENCE_FACTORS.map((f) => (
            <div key={f.label} className="flex items-center justify-between px-4 py-2.5">
              <span className="text-sm text-gray-700">{f.label}</span>
              <span className="text-sm font-semibold text-midnight">{f.total}</span>
            </div>
          ))}
          <div className="flex items-center justify-between bg-gray-50 px-4 py-2.5">
            <span className="text-sm font-semibold text-gray-900">Final Score</span>
            <span className="text-sm font-bold text-red-600">94.2%</span>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Step 4 - Decision tree                                             */
/* ------------------------------------------------------------------ */

function DecisionTree() {
  const nodes = [
    { label: 'Scam Violation', sub: '94.2% confidence', highlight: false },
    { label: 'Sensitive Category?', sub: 'Self-harm / Child Safety / Illegal', highlight: false },
    { label: 'NO', sub: 'Not a sensitive category', highlight: false, accent: true },
    { label: 'Confidence >= 90%?', sub: 'Permanent ban threshold', highlight: false },
    { label: 'YES (94.2%)', sub: 'Exceeds threshold', highlight: false, accent: true },
    { label: 'AUTONOMOUS BAN', sub: 'No human review required', highlight: true },
  ]

  return (
    <div className="flex flex-col items-center gap-2">
      {nodes.map((node, i) => (
        <div key={i} className="flex flex-col items-center">
          <div
            className={`w-64 rounded-lg border px-4 py-3 text-center transition-all ${
              node.highlight
                ? 'border-mauve bg-midnight text-white shadow-lg shadow-midnight/30'
                : node.accent
                  ? 'border-green-200 bg-green-50 text-green-800'
                  : 'border-gray-200 bg-white text-gray-900'
            }`}
          >
            <p className="text-sm font-semibold">{node.label}</p>
            <p
              className={`mt-0.5 text-xs ${
                node.highlight ? 'text-white/80' : node.accent ? 'text-green-600' : 'text-gray-500'
              }`}
            >
              {node.sub}
            </p>
          </div>
          {i < nodes.length - 1 && (
            <svg className="h-5 w-5 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
            </svg>
          )}
        </div>
      ))}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Step 5 - Enforcement summary                                       */
/* ------------------------------------------------------------------ */

const ENFORCEMENT_ACTIONS = [
  { time: 'T+0:00', action: 'Anomaly detected by Behavioral Event Processor', icon: 'detect' },
  { time: 'T+0:45', action: 'Evidence assembly completed (5 parallel tasks)', icon: 'evidence' },
  { time: 'T+1:02', action: 'Confidence scored at 94.2% (scam)', icon: 'score' },
  { time: 'T+1:05', action: 'Policy engine: autonomous permanent ban approved', icon: 'decision' },
  { time: 'T+1:08', action: 'Account permanently banned', icon: 'ban' },
  { time: 'T+1:08', action: 'All 47 active conversations terminated', icon: 'terminate' },
  { time: 'T+1:10', action: 'Device fingerprint + email hash added to cross-platform blocklist', icon: 'blocklist' },
  { time: 'T+1:11', action: 'Appeal record created, user notified', icon: 'notify' },
  { time: 'T+12:00', action: 'Full audit trail immutably logged', icon: 'audit' },
]

function EnforcementTimeline() {
  return (
    <div className="space-y-0">
      {ENFORCEMENT_ACTIONS.map((item, i) => (
        <div key={i} className="flex gap-3">
          {/* timeline rail */}
          <div className="flex flex-col items-center">
            <div
              className={`flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                i === 4
                  ? 'bg-red-500 text-white'
                  : 'bg-midnight/20 text-midnight'
              }`}
            >
              {i + 1}
            </div>
            {i < ENFORCEMENT_ACTIONS.length - 1 && (
              <div className="h-full w-px bg-gray-200" />
            )}
          </div>
          {/* content */}
          <div className="pb-4">
            <p className="text-xs font-mono text-gray-400">{item.time}</p>
            <p className={`text-sm ${i === 4 ? 'font-semibold text-red-600' : 'text-gray-700'}`}>
              {item.action}
            </p>
          </div>
        </div>
      ))}
      <div className="mt-2 flex items-center gap-2 rounded-lg bg-green-50 px-4 py-3 border border-green-200">
        <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
        </svg>
        <p className="text-sm font-medium text-green-800">Total time: 12 minutes detection-to-resolution</p>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Step 6 - Crisis response contrast                                  */
/* ------------------------------------------------------------------ */

function CrisisPanel() {
  return (
    <div className="space-y-4">
      {/* Crisis case card */}
      <div className="rounded-xl border-2 border-purple-300 bg-purple-50 shadow-sm">
        <div className="flex items-center justify-between border-b border-purple-200 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-200 text-purple-700">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z"
                />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-purple-900">Sensitive Case Detected</p>
              <p className="text-xs text-purple-600">Self-harm indicators identified</p>
            </div>
          </div>
          <span className="inline-flex items-center rounded-full bg-purple-600 px-3 py-1 text-xs font-bold uppercase tracking-wide text-white">
            Escalated to Human
          </span>
        </div>
        <div className="space-y-3 px-5 py-4">
          <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 border border-purple-100">
            <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            <span className="text-sm text-gray-700">Wellbeing resources sent within 5 minutes</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 border border-purple-100">
            <svg className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            <span className="text-sm text-gray-700">Escalated to trained human reviewer</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg bg-white px-3 py-2 border border-purple-100">
            <svg className="h-4 w-4 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            <span className="text-sm text-gray-700">Automated enforcement blocked</span>
          </div>
        </div>
      </div>

      {/* Contrast with autonomous */}
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Autonomous Case</p>
          <p className="mt-1 text-lg font-bold text-midnight">94.2%</p>
          <p className="text-xs text-gray-500">Auto-enforced</p>
        </div>
        <div className="rounded-lg border-2 border-purple-200 bg-purple-50 p-3 text-center">
          <p className="text-xs font-medium uppercase tracking-wide text-purple-400">Sensitive Case</p>
          <p className="mt-1 text-lg font-bold text-purple-700">Any %</p>
          <p className="text-xs text-purple-500">Always human</p>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Visual panel router                                                */
/* ------------------------------------------------------------------ */

function StepVisual({ step }: { step: number }) {
  switch (step) {
    case 0:
      return <PipelineDiagram />
    case 1:
      return <AnomalyCard />
    case 2:
      return <EvidencePanel />
    case 3:
      return <ConfidenceMeter />
    case 4:
      return <DecisionTree />
    case 5:
      return <EnforcementTimeline />
    case 6:
      return <CrisisPanel />
    default:
      return null
  }
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export function DemoPage() {
  const [step, setStep] = useState(0)

  const prev = useCallback(() => setStep((s) => Math.max(0, s - 1)), [])
  const next = useCallback(() => setStep((s) => Math.min(STEPS.length - 1, s + 1)), [])

  // keyboard navigation
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault()
        next()
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault()
        prev()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [next, prev])

  const current = STEPS[step]
  const isFirst = step === 0
  const isLast = step === STEPS.length - 1

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-[#1A1A1A]">
        <div className="mx-auto max-w-6xl px-6 py-8">
          {/* Progress bar */}
          <div className="mb-8">
            <ProgressBar current={step} total={STEPS.length} onSelect={setStep} />
          </div>

          {/* Step title */}
          <div className="text-center">
            <p className="mb-2 text-xs font-medium uppercase tracking-widest text-lilac">
              Step {step} of {STEPS.length - 1}
            </p>
            <h1 className="text-3xl font-bold text-white">{current.title}</h1>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="flex flex-col gap-8 lg:flex-row">
          {/* Narrative (left 60%) */}
          <div className="lg:w-3/5">
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-midnight" />
                <span className="text-xs font-semibold uppercase tracking-wide text-midnight">
                  {step === 0
                    ? 'Overview'
                    : step === 6
                      ? 'Bonus'
                      : `Pipeline Stage ${step}`}
                </span>
              </div>
              <p className="text-base leading-relaxed text-gray-700">{current.narrative}</p>

              {/* Extra context hints */}
              {step === 0 && (
                <div className="mt-6 rounded-lg bg-midnight/10 px-4 py-3 border border-midnight/20">
                  <p className="text-sm text-midnight">
                    Use the <strong>Next</strong> button or arrow keys to step through the pipeline.
                    Click any dot in the progress bar to jump to a specific step.
                  </p>
                </div>
              )}

              {isLast && (
                <div className="mt-6">
                  <Link
                    to="/"
                    className="inline-flex items-center gap-2 rounded-lg bg-midnight px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-aubergine"
                  >
                    Launch Dashboard
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                    </svg>
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Visual (right 40%) */}
          <div className="lg:w-2/5">
            <div key={step}>
              <StepVisual step={step} />
            </div>
          </div>
        </div>
      </div>

      {/* Navigation buttons */}
      <div className="sticky bottom-0 border-t border-gray-200 bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <button
            onClick={prev}
            disabled={isFirst}
            className={`flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition-colors ${
              isFirst
                ? 'cursor-not-allowed text-gray-300'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
            </svg>
            Previous
          </button>

          <span className="text-sm text-gray-400">
            {step + 1} / {STEPS.length}
          </span>

          <button
            onClick={next}
            disabled={isLast}
            className={`flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition-colors ${
              isLast
                ? 'cursor-not-allowed text-gray-300'
                : 'bg-midnight text-white shadow-sm hover:bg-aubergine'
            }`}
          >
            Next
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
