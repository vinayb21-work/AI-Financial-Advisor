import { useEffect } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { CheckCircle2, Circle, Loader2, RefreshCw } from 'lucide-react'
import { authApi, integrationApi } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { useSearchParams, useNavigate } from 'react-router-dom'

export default function SetupPrompt() {
  const { user, updateUser } = useAuthStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  // Refetch user data if just connected Hubspot
  useEffect(() => {
    const hubspotParam = searchParams.get('hubspot')
    if (hubspotParam === 'connected') {
      // Refetch user data to get updated hubspot_connected status
      authApi.getCurrentUser().then((response) => {
        updateUser(response.data)
        // Clean up URL
        setSearchParams({})
      })
    }
  }, [searchParams, updateUser, setSearchParams])

  // Poll sync status
  const { data: syncStatus, refetch } = useQuery({
    queryKey: ['syncStatus'],
    queryFn: async () => {
      const response = await integrationApi.getSyncStatus()
      return response.data
    },
    refetchInterval: 3000, // Poll every 3 seconds
  })

  // Update user object when sync status changes
  useEffect(() => {
    if (syncStatus) {
      updateUser({
        gmail_synced: syncStatus.gmail?.synced || false,
        calendar_synced: syncStatus.calendar?.synced || false,
        hubspot_synced: syncStatus.hubspot?.synced || false,
      })
    }
  }, [syncStatus, updateUser])

  const connectHubspot = async () => {
    const response = await authApi.getHubspotConnectUrl()
    window.location.href = response.data.authorization_url
  }

  const syncGmail = useMutation({
    mutationFn: () => integrationApi.syncGmail(),
    onSuccess: () => {
      // Polling will automatically update status every 3 seconds
      refetch()
    },
  })

  const syncCalendar = useMutation({
    mutationFn: () => integrationApi.syncCalendar(),
    onSuccess: () => {
      // Polling will automatically update status every 3 seconds
      refetch()
    },
  })

  const syncHubspot = useMutation({
    mutationFn: () => integrationApi.syncHubspot(),
    onSuccess: () => {
      // Polling will automatically update status every 3 seconds
      refetch()
    },
  })

  const steps = [
    {
      id: 'hubspot',
      title: 'Connect Hubspot CRM',
      description: 'Connect your Hubspot account to sync contacts and notes',
      completed: user?.hubspot_connected,
      action: connectHubspot,
      loading: false,
    },
    {
      id: 'gmail',
      title: 'Sync Gmail',
      description: 'Import your emails for the AI to understand your context',
      completed: syncStatus?.gmail?.synced || user?.gmail_synced,
      action: () => syncGmail.mutate(),
      loading: syncGmail.isPending,
      disabled: false, // Always enabled since Google is already connected
    },
    {
      id: 'calendar',
      title: 'Sync Calendar',
      description: 'Import calendar events to help schedule meetings',
      completed: syncStatus?.calendar?.synced || user?.calendar_synced,
      action: () => syncCalendar.mutate(),
      loading: syncCalendar.isPending,
      disabled: false, // Always enabled since Google is already connected
    },
    {
      id: 'hubspot-sync',
      title: 'Sync Hubspot Data',
      description: 'Import contacts and notes from Hubspot',
      completed: syncStatus?.hubspot?.synced || user?.hubspot_synced,
      action: () => syncHubspot.mutate(),
      loading: syncHubspot.isPending,
      disabled: !user?.hubspot_connected,
    },
  ]

  const allCompleted = steps.every((step) => step.completed)

  // Redirect to chat when all steps are completed
  useEffect(() => {
    if (allCompleted) {
      const timer = setTimeout(() => {
        navigate('/', { replace: true })
      }, 2000)
      
      return () => clearTimeout(timer)
    }
  }, [allCompleted, navigate])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-2xl space-y-8 rounded-2xl bg-white p-8 shadow-xl">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome to AI Financial Advisor
          </h1>
          <p className="mt-2 text-gray-600">
            Let's set up your integrations to get started
          </p>
        </div>

        <div className="space-y-4">
          {steps.map((step) => (
            <div
              key={step.id}
              className="flex items-start gap-4 rounded-lg border border-gray-200 bg-white p-4 transition hover:border-blue-300"
            >
              <div className="flex-shrink-0 pt-1">
                {step.completed ? (
                  <CheckCircle2 className="h-6 w-6 text-green-500" />
                ) : (
                  <Circle className="h-6 w-6 text-gray-300" />
                )}
              </div>

              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{step.title}</h3>
                <p className="mt-1 text-sm text-gray-600">{step.description}</p>
              </div>

              {!step.completed && (
                <button
                  onClick={step.action}
                  disabled={step.disabled || step.loading}
                  className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
                >
                  {step.loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Syncing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4" />
                      {step.id === 'hubspot' ? 'Connect' : 'Sync'}
                    </>
                  )}
                </button>
              )}
            </div>
          ))}
        </div>

        {allCompleted && (
          <div className="rounded-lg bg-green-50 p-4 text-center">
            <CheckCircle2 className="mx-auto h-8 w-8 text-green-500" />
            <p className="mt-2 font-medium text-green-900">
              All set! Redirecting to chat...
            </p>
          </div>
        )}

        <p className="text-center text-xs text-gray-500">
          This setup will take a few minutes to complete
        </p>
      </div>
    </div>
  )
}

