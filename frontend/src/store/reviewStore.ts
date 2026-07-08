import { create } from 'zustand'
import type { ReviewQueueItem, QueueDepth, Priority } from '@/types'
import { casesApi } from '@/services/casesApi'

interface ReviewState {
  queue: ReviewQueueItem[]
  totalCount: number
  queueDepth: QueueDepth | null
  loading: boolean
  error: string | null
  priorityFilter: Priority | null
  fetchQueue: (priority?: string) => Promise<void>
  setPriorityFilter: (priority: Priority | null) => void
}

export const useReviewStore = create<ReviewState>((set, get) => ({
  queue: [],
  totalCount: 0,
  queueDepth: null,
  loading: false,
  error: null,
  priorityFilter: null,

  fetchQueue: async (priority) => {
    set({ loading: true, error: null })
    try {
      const data = await casesApi.getReviewQueue(priority)
      set({
        queue: data.cases,
        totalCount: data.total_count,
        queueDepth: data.queue_depth_by_priority,
        loading: false,
      })
    } catch (e) {
      set({ error: (e as Error).message, loading: false })
    }
  },

  setPriorityFilter: (priority) => {
    set({ priorityFilter: priority })
    get().fetchQueue(priority ?? undefined)
  },
}))
