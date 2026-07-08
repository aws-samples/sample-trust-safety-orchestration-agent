import { clsx } from 'clsx'

interface ConfidenceBadgeProps {
  score: number
}

export function ConfidenceBadge({ score }: ConfidenceBadgeProps) {
  const pct = Math.round(score * 100)
  const color =
    score >= 0.9 ? 'text-red-700 bg-red-50' :
    score >= 0.75 ? 'text-orange-700 bg-orange-50' :
    score >= 0.5 ? 'text-yellow-700 bg-yellow-50' :
    'text-green-700 bg-green-50'

  return (
    <span className={clsx('inline-flex items-center rounded-md px-2 py-1 text-xs font-medium', color)}>
      {pct}%
    </span>
  )
}
