import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/lib/api'
import Button from '@/components/Button'
import Input from '@/components/Input'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function SettingsPage() {
  const navigate = useNavigate()
  const { data: user, isLoading } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getMe,
  })

  const [displayName, setDisplayName] = useState(user?.display_name || '')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || '')
    }
  }, [user])

  const handleSave = async () => {
    setSaving(true)
    // TODO: Implement update profile API call
    setSaving(false)
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-2">Customize your Dat.AI experience</p>
        </div>

        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Display Name</label>
            <Input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Enter display name"
            />
          </div>

          <div className="pt-4 flex gap-2">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
            <Button variant="outline" onClick={() => navigate('/app')}>
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

