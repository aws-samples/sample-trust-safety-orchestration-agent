import { api } from './api'
import type { ReviewerExposure } from '@/types'

export const reviewerApi = {
  getExposure: (reviewerId: string) =>
    api.get<ReviewerExposure>(`/reviewers/${reviewerId}/exposure-metrics`),
}
