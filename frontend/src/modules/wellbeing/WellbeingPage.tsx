import { useState, useEffect } from 'react'
import { reviewerApi } from '@/services/reviewerApi'
import { useAuthStore } from '@/store/authStore'
import { Card } from '@/components/Card'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import type { ReviewerExposure } from '@/types'

const DAILY_THRESHOLD = 20

function getProgressColor(percent: number): string {
  if (percent >= 80) return 'bg-red-500'
  if (percent >= 50) return 'bg-yellow-500'
  return 'bg-green-500'
}

function getProgressTrackColor(percent: number): string {
  if (percent >= 80) return 'bg-red-100'
  if (percent >= 50) return 'bg-yellow-100'
  return 'bg-green-100'
}

export function WellbeingPage() {
  const storeUserId = useAuthStore((s) => s.user?.id)
  const hasToken = useAuthStore((s) => !!s.token)
  const userId = storeUserId || (hasToken ? 'current-reviewer' : null)

  const [exposure, setExposure] = useState<ReviewerExposure | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!userId) {
      setLoading(false)
      setError('No authenticated user found.')
      return
    }

    async function fetchExposure() {
      setLoading(true)
      setError(null)
      try {
        const data = await reviewerApi.getExposure(userId!)
        setExposure(data)
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setLoading(false)
      }
    }

    fetchExposure()
  }, [userId])

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Reviewer Wellbeing</h1>
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Reviewer Wellbeing</h1>
        <Card>
          <div className="rounded-lg bg-red-50 p-4">
            <p className="text-sm font-medium text-red-700">
              Failed to load wellbeing data: {error}
            </p>
          </div>
        </Card>
      </div>
    )
  }

  if (!exposure) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Reviewer Wellbeing</h1>
        <Card>
          <p className="text-sm text-gray-500">No exposure data available.</p>
        </Card>
      </div>
    )
  }

  const harmfulToday = exposure.today.harmful_content_exposure
  const percent = Math.min(Math.round((harmfulToday / DAILY_THRESHOLD) * 100), 100)
  const progressColor = getProgressColor(percent)
  const trackColor = getProgressTrackColor(percent)

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reviewer Wellbeing</h1>
        <p className="mt-1 text-sm text-gray-500">
          Monitor your content exposure and access wellness resources.
        </p>
      </div>

      {/* Today's Summary */}
      <Card title="Today's Exposure">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div className="text-center">
            <p className="text-sm font-medium text-gray-500">Cases Reviewed</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {exposure.today.cases_reviewed}
            </p>
          </div>

          <div className="text-center">
            <p className="text-sm font-medium text-gray-500">Harmful Exposures</p>
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {harmfulToday}
              <span className="text-lg font-normal text-gray-400">
                {' '}/ {DAILY_THRESHOLD}
              </span>
            </p>
            <div className="mx-auto mt-2 w-full max-w-[160px]">
              <div className={`h-2 w-full overflow-hidden rounded-full ${trackColor}`}>
                <div
                  className={`h-full rounded-full transition-all ${progressColor}`}
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          </div>

          <div className="text-center">
            <p className="text-sm font-medium text-gray-500">Status</p>
            <div className="mt-2">
              {exposure.exposure_threshold_reached ? (
                <span className="inline-flex items-center rounded-full bg-red-100 px-3 py-1 text-sm font-semibold text-red-700">
                  Needs Break
                </span>
              ) : (
                <span className="inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-semibold text-green-700">
                  OK
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Weekly Summary */}
      <Card title="This Week">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          <div className="text-center">
            <p className="text-sm font-medium text-gray-500">Cases Reviewed</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {exposure.this_week.cases_reviewed}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-500">Harmful Exposures</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {exposure.this_week.harmful_exposure_count}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-500">Time on Sensitive Cases</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">
              {exposure.this_week.time_on_sensitive_minutes} min
            </p>
          </div>
        </div>
      </Card>

      {/* Exposure Progress */}
      <Card title="Exposure Progress">
        <div className="space-y-3">
          <div className={`h-4 w-full overflow-hidden rounded-full ${trackColor}`}>
            <div
              className={`h-full rounded-full transition-all ${progressColor}`}
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">
              {harmfulToday} of {DAILY_THRESHOLD} harmful content exposures today
            </span>
            <span className="font-medium text-gray-900">{percent}%</span>
          </div>
        </div>
      </Card>

      {/* Wellness Resources */}
      <Card title="Wellness Resources">
        <div className="space-y-4">
          {exposure.exposure_threshold_reached && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="text-sm font-semibold text-red-800">
                You've been exposed to significant harmful content. Please take a break.
              </p>
            </div>
          )}

          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Available Resources</h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="#eap"
                  className="text-sm text-midnight underline decoration-mauve hover:text-aubergine"
                >
                  Employee Assistance Program
                </a>
              </li>
              <li>
                <a
                  href="#mental-health"
                  className="text-sm text-midnight underline decoration-mauve hover:text-aubergine"
                >
                  Mental Health Resources
                </a>
              </li>
              <li>
                <a
                  href="#supervisor"
                  className="text-sm text-midnight underline decoration-mauve hover:text-aubergine"
                >
                  Supervisor Contact
                </a>
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  )
}
