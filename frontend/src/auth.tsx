import { useEffect, useState, type ReactNode } from 'react'
import { fetchCurrentUser, logout as apiLogout, type User } from './api'
import { AuthContext } from './authContext'

// Keeps track of who is logged in. The session itself lives in an HttpOnly
// cookie set by the backend; this just asks the backend who that is.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  async function logout() {
    await apiLogout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
