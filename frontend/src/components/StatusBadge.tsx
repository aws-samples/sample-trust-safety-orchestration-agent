import { clsx } from 'clsx'

const styles: Record<string, string> = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-green-100 text-green-800',
  new: 'bg-blue-100 text-blue-800',
  investigating: 'bg-purple-100 text-purple-800',
  pending_review: 'bg-yellow-100 text-yellow-800',
  in_review: 'bg-indigo-100 text-indigo-800',
  resolved: 'bg-green-100 text-green-800',
  escalated: 'bg-red-100 text-red-800',
}

interface StatusBadgeProps {
  status: string
  label?: string
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        styles[status] || 'bg-gray-100 text-gray-800',
      )}
    >
      {label || status.replace(/_/g, ' ')}
    </span>
  )
}
