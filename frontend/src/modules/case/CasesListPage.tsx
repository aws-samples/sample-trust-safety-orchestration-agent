import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useCaseStore } from '@/store/caseStore'
import { Card } from '@/components/Card'
import { StatusBadge } from '@/components/StatusBadge'
import { ConfidenceBadge } from '@/components/ConfidenceBadge'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { EmptyState } from '@/components/EmptyState'
import { formatDistanceToNow } from 'date-fns'

export function CasesListPage() {
  const { activeCases, loading, fetchActiveCases } = useCaseStore()

  useEffect(() => {
    fetchActiveCases()
  }, [fetchActiveCases])

  if (loading && activeCases.length === 0) return <LoadingSpinner />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Active Cases</h1>
        <span className="text-sm text-gray-500">{activeCases.length} cases</span>
      </div>

      <Card>
        {activeCases.length === 0 ? (
          <EmptyState title="No active cases" description="All cases have been resolved." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="pb-3 pr-4">Case ID</th>
                  <th className="pb-3 pr-4">Status</th>
                  <th className="pb-3 pr-4">Violation</th>
                  <th className="pb-3 pr-4">Confidence</th>
                  <th className="pb-3 pr-4">User</th>
                  <th className="pb-3 pr-4">Created</th>
                  <th className="pb-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {activeCases.map((c) => (
                  <tr key={c.case_id} className="hover:bg-gray-50">
                    <td className="py-3 pr-4 font-mono text-xs">{c.case_id.slice(0, 16)}...</td>
                    <td className="py-3 pr-4"><StatusBadge status={c.status} /></td>
                    <td className="py-3 pr-4 capitalize">{c.violation_type.replace(/_/g, ' ')}</td>
                    <td className="py-3 pr-4"><ConfidenceBadge score={c.confidence_score} /></td>
                    <td className="py-3 pr-4 font-mono text-xs">{c.user_id.slice(0, 12)}...</td>
                    <td className="py-3 pr-4 text-gray-500">
                      {formatDistanceToNow(new Date(c.created_at), { addSuffix: true })}
                    </td>
                    <td className="py-3">
                      <Link
                        to={`/app/cases/${c.case_id}`}
                        className="text-midnight hover:text-aubergine font-medium"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
