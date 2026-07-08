import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useCaseStore } from '@/store/caseStore'
import { casesApi } from '@/services/casesApi'
import { Card } from '@/components/Card'
import { StatusBadge } from '@/components/StatusBadge'
import { ConfidenceBadge } from '@/components/ConfidenceBadge'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { Modal } from '@/components/Modal'
import { DecisionType, EnforcementAction, SanitizationLevel } from '@/types'
import type { ReviewDecision } from '@/types'

const ACTION_LABELS: Record<EnforcementAction, string> = {
  [EnforcementAction.Warning]: 'Warning',
  [EnforcementAction.ContentRemoval]: 'Content Removal',
  [EnforcementAction.RateLimit]: 'Rate Limit',
  [EnforcementAction.TempSuspension]: 'Temporary Suspension',
  [EnforcementAction.PermanentBan]: 'Permanent Ban',
}

const SANITIZATION_OPTIONS: { value: SanitizationLevel; label: string }[] = [
  { value: SanitizationLevel.LabelsOnly, label: 'Labels Only' },
  { value: SanitizationLevel.Blurred, label: 'Blurred' },
  { value: SanitizationLevel.Full, label: 'Full' },
]

export function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const navigate = useNavigate()
  const { currentEvidence, loading, fetchEvidence, clearCurrentEvidence } = useCaseStore()

  const [sanitizationLevel, setSanitizationLevel] = useState<SanitizationLevel>(SanitizationLevel.LabelsOnly)
  const [decisionType, setDecisionType] = useState<DecisionType | null>(null)
  const [selectedAction, setSelectedAction] = useState<EnforcementAction>(EnforcementAction.Warning)
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSuccessModal, setShowSuccessModal] = useState(false)

  useEffect(() => {
    if (caseId) {
      fetchEvidence(caseId, sanitizationLevel)
    }
    return () => clearCurrentEvidence()
  }, [caseId, sanitizationLevel, fetchEvidence, clearCurrentEvidence])

  const handleSubmit = async () => {
    if (!caseId || !decisionType) return
    setSubmitting(true)
    setError(null)

    const decision: ReviewDecision = {
      decision: decisionType,
      notes: notes || undefined,
    }
    if (decisionType === DecisionType.ApproveAction) {
      decision.action = selectedAction
    }

    try {
      await casesApi.submitDecision(caseId, decision)
      setShowSuccessModal(true)
      setTimeout(() => navigate('/app/review'), 2000)
    } catch (e) {
      setError((e as Error).message || 'Failed to submit decision')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading && !currentEvidence) {
    return <LoadingSpinner />
  }

  const evidence = currentEvidence
  const profile = evidence?.profile_metadata
  const contentAnalysis = evidence?.content_analysis
  const messageHistory = evidence?.message_history
  const imageAnalysis = evidence?.image_analysis
  const crossPlatform = evidence?.cross_platform_intelligence

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          <svg className="mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          Back
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          Case <span className="font-mono text-lg text-gray-600">{caseId}</span>
        </h1>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Evidence Panel — left 2/3 */}
        <div className="col-span-2 space-y-6">
          {/* Profile Metadata */}
          {profile && (
            <Card title="Profile Metadata">
              <dl className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
                <div>
                  <dt className="font-medium text-gray-500">Display Name</dt>
                  <dd className="mt-1 text-gray-900">{profile.display_name ?? '--'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">Account Age</dt>
                  <dd className="mt-1 text-gray-900">
                    {profile.account_age_days != null ? `${profile.account_age_days} days` : '--'}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">Verification</dt>
                  <dd className="mt-1">
                    {profile.verification_status ? (
                      <StatusBadge status={profile.verification_status} />
                    ) : (
                      <span className="text-gray-400">--</span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">Photos</dt>
                  <dd className="mt-1 text-gray-900">{profile.photo_count ?? '--'}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="font-medium text-gray-500">Profile Completeness</dt>
                  <dd className="mt-2">
                    {profile.profile_completeness != null ? (
                      <div className="flex items-center gap-3">
                        <div className="h-2 flex-1 rounded-full bg-gray-100">
                          <div
                            className="h-2 rounded-full bg-midnight transition-all"
                            style={{ width: `${Math.round(profile.profile_completeness * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-gray-600">
                          {Math.round(profile.profile_completeness * 100)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-400">--</span>
                    )}
                  </dd>
                </div>
              </dl>
            </Card>
          )}

          {/* Content Analysis */}
          {contentAnalysis && (
            <Card title="Content Analysis">
              <div className="space-y-4">
                {([
                  { key: 'scam_indicators' as const, label: 'Scam Indicators' },
                  { key: 'threat_indicators' as const, label: 'Threat Indicators' },
                  { key: 'crisis_indicators' as const, label: 'Crisis Indicators' },
                ] as const).map(({ key, label }) => {
                  const indicators = contentAnalysis[key]
                  if (!indicators || indicators.length === 0) return null
                  return (
                    <div key={key}>
                      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">{label}</h4>
                      <ul className="space-y-2">
                        {indicators.map((ind, i) => (
                          <li key={i} className="flex items-start gap-2 rounded-md border border-gray-100 bg-gray-50 px-3 py-2 text-sm">
                            <StatusBadge status={ind.severity} />
                            <div>
                              <span className="font-medium text-gray-900">{ind.type}</span>
                              {ind.pattern && (
                                <span className="ml-2 text-gray-500">- {ind.pattern}</span>
                              )}
                              {ind.context && (
                                <p className="mt-0.5 text-xs text-gray-400">{ind.context}</p>
                              )}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )
                })}
                {contentAnalysis.sentiment && (
                  <div>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">Sentiment</h4>
                    <div className="flex gap-4 text-sm">
                      <span className="text-gray-600">
                        Overall: <span className="font-medium text-gray-900">{contentAnalysis.sentiment.overall}</span>
                      </span>
                      <span className="text-gray-600">
                        Manipulation: <span className="font-medium text-gray-900">{Math.round(contentAnalysis.sentiment.manipulation_score * 100)}%</span>
                      </span>
                      <span className="text-gray-600">
                        Aggression: <span className="font-medium text-gray-900">{Math.round(contentAnalysis.sentiment.aggression_score * 100)}%</span>
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Message History */}
          {messageHistory && (
            <Card title={`Message History (${messageHistory.total_count})`}>
              {messageHistory.messages.length === 0 ? (
                <p className="text-sm text-gray-400">No messages available.</p>
              ) : (
                <div className="max-h-80 space-y-3 overflow-y-auto">
                  {messageHistory.messages.map((msg) => (
                    <div
                      key={msg.message_id}
                      className={`rounded-lg border px-3 py-2 text-sm ${
                        msg.flagged
                          ? 'border-red-200 bg-red-50'
                          : 'border-gray-100 bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <span>{msg.recipient_id ? `To: ${msg.recipient_id}` : 'Message'}</span>
                        <span>{formatTimestamp(msg.sent_at)}</span>
                      </div>
                      <p className="mt-1 text-gray-800">
                        {sanitizationLevel === SanitizationLevel.LabelsOnly
                          ? '[Content hidden]'
                          : msg.content}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}

          {/* Image Analysis */}
          {imageAnalysis && imageAnalysis.profile_images.length > 0 && (
            <Card title="Image Analysis">
              <div className="grid grid-cols-2 gap-4">
                {imageAnalysis.profile_images.map((img) => (
                  <div
                    key={img.image_id}
                    className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm"
                  >
                    <p className="mb-2 font-mono text-xs text-gray-400">{img.image_id}</p>
                    <div className="flex flex-wrap gap-2">
                      {img.is_ai_generated && (
                        <StatusBadge status="high" label="AI Generated" />
                      )}
                      {img.is_stock_photo && (
                        <StatusBadge status="medium" label="Stock Photo" />
                      )}
                      {img.reverse_search_matches != null && img.reverse_search_matches > 0 && (
                        <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                          {img.reverse_search_matches} reverse matches
                        </span>
                      )}
                      {!img.is_ai_generated && !img.is_stock_photo && (img.reverse_search_matches == null || img.reverse_search_matches === 0) && (
                        <span className="text-xs text-gray-400">No flags</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Cross-Platform Intelligence */}
          {crossPlatform && (
            <Card title="Cross-Platform Intelligence">
              <dl className="grid grid-cols-3 gap-x-6 gap-y-4 text-sm">
                <div>
                  <dt className="font-medium text-gray-500">Match Type</dt>
                  <dd className="mt-1 text-gray-900">{crossPlatform.match_type}</dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">Confidence</dt>
                  <dd className="mt-1">
                    <ConfidenceBadge score={crossPlatform.confidence} />
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-gray-500">Source Platform</dt>
                  <dd className="mt-1 text-gray-900">{crossPlatform.source_platform}</dd>
                </div>
                {crossPlatform.ban_reason && (
                  <div className="col-span-3">
                    <dt className="font-medium text-gray-500">Ban Reason</dt>
                    <dd className="mt-1 text-gray-900">{crossPlatform.ban_reason}</dd>
                  </div>
                )}
              </dl>
            </Card>
          )}

          {/* Sanitization Level Toggle */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-600">Content Visibility:</span>
            <div className="inline-flex rounded-lg border border-gray-200 bg-white">
              {SANITIZATION_OPTIONS.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => setSanitizationLevel(value)}
                  className={`px-4 py-2 text-sm font-medium transition-colors first:rounded-l-lg last:rounded-r-lg ${
                    sanitizationLevel === value
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Decision Panel — right 1/3 */}
        <div className="space-y-6">
          <Card title="Decision">
            <div className="space-y-4">
              {/* Decision Buttons */}
              <div className="space-y-2">
                <button
                  onClick={() => setDecisionType(DecisionType.ApproveAction)}
                  className={`w-full rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors ${
                    decisionType === DecisionType.ApproveAction
                      ? 'border-midnight bg-midnight/10 text-midnight'
                      : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Approve Suggested Action
                </button>
                <button
                  onClick={() => setDecisionType(DecisionType.Dismiss)}
                  className={`w-full rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors ${
                    decisionType === DecisionType.Dismiss
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Dismiss
                </button>
                <button
                  onClick={() => setDecisionType(DecisionType.Escalate)}
                  className={`w-full rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors ${
                    decisionType === DecisionType.Escalate
                      ? 'border-red-500 bg-red-50 text-red-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Escalate
                </button>
              </div>

              {/* Action Dropdown (shown for Approve) */}
              {decisionType === DecisionType.ApproveAction && (
                <div>
                  <label htmlFor="action-select" className="mb-1 block text-xs font-medium text-gray-500">
                    Enforcement Action
                  </label>
                  <select
                    id="action-select"
                    value={selectedAction}
                    onChange={(e) => setSelectedAction(e.target.value as EnforcementAction)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
                  >
                    {Object.values(EnforcementAction).map((action) => (
                      <option key={action} value={action}>
                        {ACTION_LABELS[action]}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Notes */}
              <div>
                <label htmlFor="decision-notes" className="mb-1 block text-xs font-medium text-gray-500">
                  Notes
                </label>
                <textarea
                  id="decision-notes"
                  rows={4}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add context or reasoning for this decision..."
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                onClick={handleSubmit}
                disabled={!decisionType || submitting}
                className="w-full rounded-lg bg-midnight px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-aubergine disabled:cursor-not-allowed disabled:opacity-50"
              >
                {submitting ? 'Submitting...' : 'Submit Decision'}
              </button>
            </div>
          </Card>
        </div>
      </div>

      {/* Success Modal */}
      <Modal
        open={showSuccessModal}
        onClose={() => setShowSuccessModal(false)}
        title="Decision Submitted"
      >
        <div className="text-center">
          <svg className="mx-auto mb-3 h-12 w-12 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-gray-600">
            Your decision has been recorded. Redirecting to the review queue...
          </p>
        </div>
      </Modal>
    </div>
  )
}

function formatTimestamp(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}
