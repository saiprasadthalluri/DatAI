import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/lib/api'
import Button from '@/components/Button'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { data: user, isLoading } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getMe,
  })

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Profile</h1>
          <p className="text-muted-foreground mt-2">Your data science expert profile</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Email</label>
            <p className="text-lg">{user?.email}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Display Name</label>
            <p className="text-lg">{user?.display_name || 'Not set'}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Member Since</label>
            <p className="text-lg">{new Date(user?.created_at).toLocaleDateString()}</p>
          </div>

          <div className="pt-4">
            <Button onClick={() => navigate('/settings')}>Edit Profile</Button>
          </div>
        </div>
      </div>
    </div>
  )
}


