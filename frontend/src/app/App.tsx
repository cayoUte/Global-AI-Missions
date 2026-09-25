import { QueryClientProvider, type QueryClient } from '@tanstack/react-query'
import { MotionConfig } from 'framer-motion'
import { Navigate, Route, Routes } from 'react-router'

import { CheckInPage } from '../features/auth/CheckInPage'
import { RequireRole, SessionWatcher } from '../features/auth/guards'
import { MissionPlayerPage } from '../features/mission/MissionPlayerPage'
import { ProgressPage } from '../features/progress/ProgressPage'
import { ReportPage } from '../features/report/ReportPage'
import { TeacherLanding } from '../features/teacher/TeacherLanding'
import { WorldPage } from '../features/world/WorldPage'
import { NotFoundPage } from '../routes/NotFoundPage'

export function AppRoutes() {
  return (
    <>
      <SessionWatcher />
      <Routes>
        <Route path="/" element={<Navigate to="/world" replace />} />
        <Route path="/check-in" element={<CheckInPage />} />
        <Route
          path="/world"
          element={
            <RequireRole roles={['student']}>
              <WorldPage />
            </RequireRole>
          }
        />
        <Route
          path="/missions/:missionId/play"
          element={
            <RequireRole roles={['student']}>
              <MissionPlayerPage />
            </RequireRole>
          }
        />
        <Route
          path="/attempts/:attemptId/report"
          element={
            <RequireRole roles={['student']}>
              <ReportPage />
            </RequireRole>
          }
        />
        <Route
          path="/progress"
          element={
            <RequireRole roles={['student']}>
              <ProgressPage />
            </RequireRole>
          }
        />
        <Route
          path="/teacher"
          element={
            <RequireRole roles={['teacher', 'admin']}>
              <TeacherLanding />
            </RequireRole>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  )
}

export function App({ queryClient }: { queryClient: QueryClient }) {
  return (
    <QueryClientProvider client={queryClient}>
      <MotionConfig reducedMotion="user">
        <AppRoutes />
      </MotionConfig>
    </QueryClientProvider>
  )
}
