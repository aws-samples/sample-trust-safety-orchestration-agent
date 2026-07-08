import { api } from './api'

export const auditApi = {
  exportLogs: (startDate: string, endDate: string, format: 'json' | 'csv' = 'json') =>
    api.get<{ download_url: string }>(
      `/audit/export?start_date=${startDate}&end_date=${endDate}&format=${format}`,
    ),
}
