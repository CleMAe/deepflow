import { Navigate, useLocation } from 'react-router-dom'
import { useUserStore } from '@/stores/userStore'

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = useUserStore((s) => s.token)
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
