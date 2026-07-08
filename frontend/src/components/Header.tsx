import { useMetricsStore } from '@/store/metricsStore'
import { useAuthStore } from '@/store/authStore'
import { StatusBadge } from './StatusBadge'

export function Header() {
  const metrics = useMetricsStore((s) => s.metrics)
  const logout = useAuthStore((s) => s.logout)

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div className="flex items-center gap-4">
        {metrics?.elevated_threat_level && (
          <StatusBadge status="critical" label="ELEVATED THREAT" />
        )}
        {metrics && (
          <span className="text-sm text-gray-500">
            Queue: <span className="font-medium text-gray-900">{metrics.review_queue_depth}</span>
          </span>
        )}
      </div>

      <button
        onClick={logout}
        className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        Sign out
      </button>
    </header>
  )
}
