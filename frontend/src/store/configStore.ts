import { create } from 'zustand'
import type { ConfigEntry } from '@/types'
import { configApi } from '@/services/configApi'

interface ConfigState {
  configs: ConfigEntry[]
  loading: boolean
  error: string | null
  fetchConfigs: () => Promise<void>
  rollback: (configKey: string, versionId: string) => Promise<void>
}

export const useConfigStore = create<ConfigState>((set) => ({
  configs: [],
  loading: false,
  error: null,

  fetchConfigs: async () => {
    set({ loading: true, error: null })
    try {
      const raw = await configApi.getCurrent()
      const configsMap = raw.configs as unknown as Record<string, string>
      const entries: ConfigEntry[] = Object.entries(configsMap).map(([key, val]) => {
        let parsed: Record<string, unknown> = {}
        try { parsed = typeof val === 'string' ? JSON.parse(val) : val as Record<string, unknown> } catch { /* */ }
        return {
          config_key: key,
          value: parsed,
          version_id: '',
          is_active: true,
          updated_by: 'system',
          updated_at: new Date().toISOString(),
        }
      })
      set({ configs: entries, loading: false })
    } catch (e) {
      set({ error: (e as Error).message, loading: false })
    }
  },

  rollback: async (configKey, versionId) => {
    set({ loading: true, error: null })
    try {
      await configApi.rollback(configKey, versionId)
      await useConfigStore.getState().fetchConfigs()
      set({ loading: false })
    } catch (e) {
      set({ error: (e as Error).message, loading: false })
    }
  },
}))
