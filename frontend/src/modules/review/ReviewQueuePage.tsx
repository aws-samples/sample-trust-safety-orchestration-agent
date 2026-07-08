import { useReviewStore } from '@/store/reviewStore'
import { Card } from '@/components/Card'
import { StatusBadge } from '@/components/StatusBadge'
import { ConfidenceBadge } from '@/components/ConfidenceBadge'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { EmptyState } from '@/components/EmptyState'
import { usePolling } from '@/hooks/usePolling'
import { Link } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { Priority } from '@/types'

const PRIORITY_LEVELS: { value: Priority; label: string; borderColor: string; textColor: string }[] = [
  { value: Priority.Critical, label: 'Critical', borderColor: 'border-l-red-500', textColor: 'text-red-700' },
  { value: Priority.High, label: 'High', borderColor: 'border-l-orange-500', textColor: 'text-orange-700' },
  { value: Priority.Medium, label: 'Medium', borderColor: 'border-l-yellow-500', textColor: 'text-yellow-700' },
  { value: Priority.Low, label: 'Low', borderColor: 'border-l-green-500', textColor: 'text-green-700' },
]

const FILTER_OPTIONS: { value: Priority | null; label: string }[] = [
  { value: null, label: 'All' },
  { value: Priority.Critical, label: 'Critical' },
  { value: Priority.High, label: 'High' },
  { value: Priority.Medium, label: 'Medium' },
  { value: Priority.Low, label: 'Low' },
]

export function ReviewQueuePage() {
  const {
    queue,
    totalCount,
    queueDepth,
    loading,
    priorityFilter,
    fetchQueue,
    setPriorityFilter,
  } = useReviewStore()

  usePolling(() => {
    fetchQueue(priorityFilter ?? undefined)
  }, 15_000)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Review Queue</h1>
        <span className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">
          {totalCount}
        </span>
      </div>

      {/* Queue Depth Summary */}
      {queueDepth && (
        <div className="grid grid-cols-4 gap-4">
          {PRIORITY_LEVELS.map(({ value, label, borderColor, textColor }) => (
            <div
              key={value}
              className={`rounded-lg border border-gray-200 border-l-4 ${borderColor} bg-white px-4 py-3 shadow-sm`}
            >
              <p className="text-xs font-medium text-gray-500">{label}</p>
              <p className={`mt-1 text-2xl font-semibold ${textColor}`}>
                {queueDepth[value as keyof typeof queueDepth]}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Priority Filter Buttons */}
      <div className="flex gap-2">
        {FILTER_OPTIONS.map(({ value, label }) => {
          const isActive = priorityFilter === value
          return (
            <button
              key={label}
              onClick={() => setPriorityFilter(value)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {label}
            </button>
          )
        })}
      </div>

      {/* Queue Table */}
      {loading && queue.length === 0 ? (
        <LoadingSpinner />
      ) : queue.length === 0 ? (
        <Card>
          <EmptyState title="No cases in queue" description="All caught up! Check back soon." />
        </Card>
      ) : (
        <Card>
          <div className="-mx-6 -my-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">Priority</th>
                  <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">Violation</th>
                  <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">Confidence</th>
                  <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">User</th>
                  <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">Created</th>
                  <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500">Est. Time</th>
                  <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-500" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {queue.map((item) => (
                  <tr key={item.queue_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <StatusBadge status={item.priority} />
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-900">
                      {item.violation_type.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-4">
                      <ConfidenceBadge score={item.confidence_score} />
                    </td>
                    <td className="px-6 py-4 text-gray-600 font-mono text-xs">
                      {item.user_id}
                    </td>
                    <td className="px-6 py-4 text-gray-500">
                      {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                    </td>
                    <td className="px-6 py-4 text-gray-500">
                      {item.estimated_review_minutes != null
                        ? `${item.estimated_review_minutes} min`
                        : '--'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/app/cases/${item.case_id}`}
                        className="inline-flex items-center rounded-md bg-midnight/10 px-3 py-1.5 text-xs font-medium text-midnight hover:bg-midnight/20 transition-colors"
                      >
                        Review
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
