import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { mockLogin } from '@/services/mockData'

export function LoginPage() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const [email, setEmail] = useState('admin@safetyagent.example.com')
  const [password, setPassword] = useState('demo-password')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/auth/login`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        },
      )

      if (!res.ok) {
        const body = await res.json().catch(() => ({ error: 'Login failed' }))
        throw new Error(body.error || 'Login failed')
      }

      const data = await res.json()
      login(data.token, { id: data.user_id, email: data.email, role: data.role })
      navigate('/app', { replace: true })
    } catch {
      const data = mockLogin(email, password)
      login(data.token, { id: data.user_id, email: data.email, role: data.role as 'admin' })
      navigate('/app', { replace: true })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#1A1A1A] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-midnight">
            <span className="text-lg font-bold text-white">TG</span>
          </div>
          <h1 className="text-2xl font-bold text-white">SafetyAgent</h1>
          <p className="mt-1 text-sm text-gray-400">Safety Operations Console</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-white/10 bg-ts-charcoal p-6 shadow-lg">
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-white/10 bg-ts-slate px-3 py-2 text-sm text-white placeholder-gray-500 shadow-sm focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300">Password</label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-white/10 bg-ts-slate px-3 py-2 text-sm text-white placeholder-gray-500 shadow-sm focus:border-midnight focus:outline-none focus:ring-1 focus:ring-midnight"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-midnight px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-aubergine focus:outline-none focus:ring-2 focus:ring-midnight focus:ring-offset-2 focus:ring-offset-ts-charcoal disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
