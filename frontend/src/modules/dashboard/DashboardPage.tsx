import { useEffect, useMemo } from 'react'
import { formatDistanceToNow } from 'date-fns'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { useMetricsStore } from '@/store/metricsStore'
import { usePolling } from '@/hooks/usePolling'
import { Card } from '@/components/Card'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { StatusBadge } from '@/components/StatusBadge'

const COLORS = [
  '#3E1768',
  '#67295F',
  '#75457D',
  '#097270',
  '#025656',
  '#D45847',
  '#9F81A5',
]

function safetyScoreColor(score: number): string {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-500'
  return 'text-red-600'
}

function safetyScoreBg(score: number): string {
  if (score >= 80) return 'bg-green-50'
  if (score >= 60) return 'bg-yellow-50'
  return 'bg-red-50'
}

function formatLabel(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function DashboardPage() {
  const { metrics, recentActions, loading, error, fetchMetrics, fetchRecentActions } =
    useMetricsStore()

  useEffect(() => {
    fetchRecentActions()
  }, [fetchRecentActions])

  usePolling(fetchMetrics, 3000)

  usePolling(fetchRecentActions, 3000)

  const threatData = useMemo(() => {
    if (!metrics?.threat_distribution) return []
    return Object.entries(metrics.threat_distribution).map(([name, value]) => ({
      name: formatLabel(name),
      value,
    }))
  }, [metrics?.threat_distribution])

  const stageData = useMemo(() => {
    if (!metrics?.active_cases_by_stage) return []
    return Object.entries(metrics.active_cases_by_stage).map(([name, value]) => ({
      name: formatLabel(name),
      value,
    }))
  }, [metrics?.active_cases_by_stage])

  if (loading && !metrics) {
    return <LoadingSpinner />
  }

  if (error && !metrics) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-4 text-sm text-red-700">
          Failed to load metrics: {error}
        </div>
      </div>
    )
  }

  if (!metrics) {
    return <LoadingSpinner />
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {metrics.elevated_threat_level && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-300 bg-red-600 px-6 py-4 text-white shadow-sm">
          <svg
            className="h-5 w-5 flex-shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
            />
          </svg>
          <span className="text-sm font-semibold">
            Elevated Threat Level Detected — Coordinated attack patterns identified. Enhanced
            monitoring is active.
          </span>
        </div>
      )}

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Trust &amp; Safety Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Real-time platform safety monitoring</p>
      </div>

      {/* Top row: 4 stat cards */}
      <div className="mb-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <div className={`rounded-lg p-2 ${safetyScoreBg(metrics.platform_safety_score)}`}>
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
              Platform Safety Score
            </p>
            <p className={`mt-1 text-4xl font-bold ${safetyScoreColor(metrics.platform_safety_score)}`}>
              {metrics.platform_safety_score}
            </p>
            <p className="mt-1 text-xs text-gray-400">out of 100</p>
          </div>
        </Card>

        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
            Cases Processed Today
          </p>
          <p className="mt-1 text-4xl font-bold text-gray-900">
            {metrics.cases_processed_today.toLocaleString()}
          </p>
        </Card>

        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
            Autonomous Resolution Rate
          </p>
          <p className="mt-1 text-4xl font-bold text-gray-900">
            {(metrics.autonomous_resolution_rate * 100).toFixed(1)}%
          </p>
          <p className="mt-1 text-xs text-gray-400">target: configurable</p>
        </Card>

        <Card>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
            Avg Resolution Time
          </p>
          <p className="mt-1 text-4xl font-bold text-gray-900">
            {metrics.avg_resolution_time_minutes.toFixed(1)}
          </p>
          <p className="mt-1 text-xs text-gray-400">minutes</p>
        </Card>
      </div>

      {/* Second row: charts */}
      <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Threat Distribution">
          {threatData.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={threatData} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fontSize: 12 }}
                    width={120}
                  />
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #e5e7eb',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {threatData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="py-8 text-center text-sm text-gray-400">No threat data available</p>
          )}
        </Card>

        <Card title="Active Cases by Stage">
          {stageData.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={stageData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }) =>
                      `${name} (${(percent * 100).toFixed(0)}%)`
                    }
                    labelLine={{ stroke: '#9ca3af' }}
                  >
                    {stageData.map((_, index) => (
                      <Cell key={index} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      borderRadius: '8px',
                      border: '1px solid #e5e7eb',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="py-8 text-center text-sm text-gray-400">No active cases</p>
          )}
        </Card>
      </div>

      {/* Third row: Review Queue Depth */}
      <div className="mb-6">
        <Card title="Review Queue Depth">
          <div className="flex items-center gap-4">
            <p className="text-5xl font-bold text-gray-900">
              {metrics.review_queue_depth.toLocaleString()}
            </p>
            <div className="text-sm text-gray-500">
              {metrics.review_queue_depth === 0 ? (
                <StatusBadge status="resolved" label="Queue Clear" />
              ) : metrics.review_queue_depth > 50 ? (
                <StatusBadge status="critical" label="High Volume" />
              ) : (
                <StatusBadge status="medium" label="Normal" />
              )}
              <p className="mt-1">cases awaiting human review</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Bottom: Recent Actions table */}
      <Card title="Recent Enforcement Actions">
        {recentActions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="pb-3 pr-4 font-medium text-gray-500">Log ID</th>
                  <th className="pb-3 pr-4 font-medium text-gray-500">Action</th>
                  <th className="pb-3 pr-4 font-medium text-gray-500">Violation Type</th>
                  <th className="pb-3 pr-4 font-medium text-gray-500">Case ID</th>
                  <th className="pb-3 font-medium text-gray-500">When</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {recentActions.map((entry) => (
                  <tr key={entry.log_id} className="hover:bg-gray-50">
                    <td className="py-3 pr-4 font-mono text-xs text-gray-600">
                      {entry.log_id.slice(0, 12)}...
                    </td>
                    <td className="py-3 pr-4">
                      {entry.action ? (
                        <StatusBadge status={entry.action} />
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 pr-4">
                      {entry.violation_type ? (
                        formatLabel(entry.violation_type)
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 font-mono text-xs text-gray-600">
                      {entry.case_id ? `${entry.case_id.slice(0, 12)}...` : '-'}
                    </td>
                    <td className="py-3 text-gray-500">
                      {formatDistanceToNow(new Date(entry.timestamp), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-gray-400">No recent actions</p>
        )}
      </Card>
    </div>
  )
}
