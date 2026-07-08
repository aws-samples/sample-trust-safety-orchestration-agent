import { api } from './api'
import type { RealtimeMetrics, AuditLogEntry, ComplianceReport } from '@/types'

export const metricsApi = {
  getRealtime: () =>
    api.get<RealtimeMetrics>('/metrics/realtime'),

  getRecentActions: () =>
    api.get<{ recent_actions: AuditLogEntry[] }>('/actions/recent'),

  getComplianceReport: (startDate: string, endDate: string) =>
    api.get<ComplianceReport>(
      `/reports/compliance?start_date=${startDate}&end_date=${endDate}`,
    ),
}
