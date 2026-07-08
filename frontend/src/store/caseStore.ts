import { create } from 'zustand'
import type { Case, EvidencePackage, SanitizationLevel } from '@/types'
import { casesApi } from '@/services/casesApi'

interface CaseState {
  activeCases: Case[]
  currentEvidence: EvidencePackage | null
  loading: boolean
  error: string | null
  fetchActiveCases: () => Promise<void>
  fetchEvidence: (caseId: string, visibility?: SanitizationLevel) => Promise<void>
  clearCurrentEvidence: () => void
}

export const useCaseStore = create<CaseState>((set) => ({
  activeCases: [],
  currentEvidence: null,
  loading: false,
  error: null,

  fetchActiveCases: async () => {
    set({ loading: true, error: null })
    try {
      const { cases } = await casesApi.getActiveCases()
      set({ activeCases: cases, loading: false })
    } catch (e) {
      set({ error: (e as Error).message, loading: false })
    }
  },

  fetchEvidence: async (caseId, visibility) => {
    set({ loading: true, error: null })
    try {
      const data = await casesApi.getEvidence(caseId, visibility)
      set({ currentEvidence: data.evidence, loading: false })
    } catch (e) {
      set({ error: (e as Error).message, loading: false })
    }
  },

  clearCurrentEvidence: () => set({ currentEvidence: null }),
}))
