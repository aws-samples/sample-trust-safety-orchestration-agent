import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Layout } from '@/components/Layout'
import { LoginPage } from '@/components/LoginPage'
import { DemoPage } from '@/modules/demo/DemoPage'
import { DashboardPage } from '@/modules/dashboard/DashboardPage'
import { ReviewQueuePage } from '@/modules/review/ReviewQueuePage'
import { CasesListPage } from '@/modules/case/CasesListPage'
import { CaseDetailPage } from '@/modules/case/CaseDetailPage'
import { AdminConfigPage } from '@/modules/admin/AdminConfigPage'
import { WellbeingPage } from '@/modules/wellbeing/WellbeingPage'
import { GettingStartedPage } from '@/modules/getting-started/GettingStartedPage'
import type { ReactNode } from 'react'

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AuthenticatedApp() {
  useWebSocket()

  useEffect(() => {
    document.documentElement.classList.remove('dark')
  }, [])

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="review" element={<ReviewQueuePage />} />
        <Route path="cases" element={<CasesListPage />} />
        <Route path="cases/:caseId" element={<CaseDetailPage />} />
        <Route path="admin" element={<AdminConfigPage />} />
        <Route path="wellbeing" element={<WellbeingPage />} />
        <Route path="getting-started" element={<GettingStartedPage />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/demo" element={<DemoPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/app/*"
        element={
          <ProtectedRoute>
            <AuthenticatedApp />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
