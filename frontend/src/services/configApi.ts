import { api } from './api'
import type { ConfigEntry, ThresholdConfig } from '@/types'

export const configApi = {
  getCurrent: () =>
    api.get<{ configs: ConfigEntry[] }>('/config/current'),

  updateThresholds: (config: ThresholdConfig) =>
    api.put<{ config_key: string; version_id: string; status: string }>(
      '/config/thresholds',
      config,
    ),

  rollback: (configKey: string, versionId: string) =>
    api.post<{ config_key: string; new_version_id: string; status: string }>(
      '/config/rollback',
      { config_key: configKey, version_id: versionId },
    ),
}
