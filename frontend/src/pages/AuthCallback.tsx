import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../lib/api'
import { Loader2 } from 'lucide-react'

export default function AuthCallback() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { setAuth } = useAuthStore()

  useEffect(() => {
    const token = searchParams.get('token')

    if (token) {
      // Set token and fetch user data
      setAuth(token, null as any)
      
      // Fetch user data immediately
      authApi
        .getCurrentUser()
        .then((response) => {
          setAuth(token, response.data)
          navigate('/')
        })
        .catch((error) => {
          console.error('Error fetching user:', error)
          navigate('/login')
        })
    } else {
      navigate('/login')
    }
  }, [searchParams, setAuth, navigate])

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600" />
        <p className="mt-4 text-gray-600">Authenticating...</p>
      </div>
    </div>
  )
}

