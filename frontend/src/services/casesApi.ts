import { api } from './api'
import type {
  Case,
  EvidencePackage,
  ReviewQueueItem,
  ReviewDecision,
  QueueDepth,
  EnforcementResult,
  SanitizationLevel,
} from '@/types'

export const casesApi = {
  getActiveCases: () =>
    api.get<{ cases: Case[] }>('/cases/active'),

  getEvidence: (caseId: string, visibility: SanitizationLevel = 'labels_only' as SanitizationLevel) =>
    api.get<{ case_id: string; evidence: EvidencePackage }>(
      `/cases/${caseId}/evidence?visibility=${visibility}`,
    ),

  getReviewQueue: (priority?: string, limit = 20) => {
    const params = new URLSearchParams({ limit: String(limit) })
    if (priority) params.set('priority', priority)
    return api.get<{
      cases: ReviewQueueItem[]
      total_count: number
      queue_depth_by_priority: QueueDepth
    }>(`/review-queue?${params}`)
  },

  submitDecision: (caseId: string, decision: ReviewDecision) =>
    api.post<EnforcementResult>(`/cases/${caseId}/decision`, decision),
}
