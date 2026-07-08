import { create } from 'zustand'
import type { RealtimeMetrics, AuditLogEntry } from '@/types'
import { metricsApi } from '@/services/metricsApi'

interface MetricsState {
  metrics: RealtimeMetrics | null
  recentActions: AuditLogEntry[]
  loading: boolean
  error: string | null
  fetchMetrics: () => Promise<void>
  fetchRecentActions: () => Promise<void>
  updateFromWebSocket: (data: RealtimeMetrics) => void
}

export const useMetricsStore = create<MetricsState>((set) => ({
  metrics: null,
  recentActions: [],
  loading: false,
  error: null,

  fetchMetrics: async () => {
    set({ loading: true, error: null })
    try {
      const metrics = await metricsApi.getRealtime()
      set({ metrics, loading: false })
    } catch (e) {
      set({ loading: false })
    }
  },

  fetchRecentActions: async () => {
    try {
      const { recent_actions } = await metricsApi.getRecentActions()
      set({ recentActions: recent_actions })
    } catch {
      // silent — table shows empty state
    }
  },

  updateFromWebSocket: (data) => {
    set({ metrics: data })
  },
}))
