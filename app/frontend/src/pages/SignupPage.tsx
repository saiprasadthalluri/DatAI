import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { auth, isDevMode, isBackendAuth } from '@/lib/firebase'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Logo from '@/components/Logo'
import { BarChart3, Mail, Lock, User, Chrome, TrendingUp, Database } from 'lucide-react'

export default function SignupPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleEmailSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Validate inputs
    if (!email.trim()) {
      setError('Please enter your email address')
      setLoading(false)
      return
    }
    if (!password.trim()) {
      setError('Please enter a password')
      setLoading(false)
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      setLoading(false)
      return
    }

    try {
      if (isDevMode || isBackendAuth) {
        // Use auth object's method directly (dev mode or backend auth)
        await auth.createUserWithEmailAndPassword(email.trim(), password, displayName.trim() || undefined)
      } else {
        // Use Firebase Auth
        const { createUserWithEmailAndPassword } = await import('firebase/auth')
        await createUserWithEmailAndPassword(auth, email.trim(), password)
      }
      navigate('/app')
    } catch (err: any) {
      setError(err.message || 'Failed to create account')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignup = async () => {
    setLoading(true)
    setError('')

    try {
      if (isDevMode || isBackendAuth) {
        // Dev mode or backend auth doesn't support Google sign-in
        setError('Google sign-in is not available. Please use email/password sign-up.')
        setLoading(false)
        return
      } else {
        const { signInWithPopup, GoogleAuthProvider } = await import('firebase/auth')
        const provider = new GoogleAuthProvider()
        await signInWithPopup(auth, provider)
        navigate('/app')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to sign up with Google')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-secondary/20 gradient-mesh relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      <div className="w-full max-w-md p-8 space-y-8 relative z-10 animate-fade-in">
        {/* Logo and Header */}
        <div className="text-center space-y-4">
          <div className="flex justify-center mb-4">
            <Logo size="lg" />
          </div>
          <h1 className="text-4xl font-bold text-gradient">Create an account</h1>
          <p className="text-muted-foreground text-lg">Join Dat.AI and unlock expert data science guidance</p>
        </div>

        {/* Signup Form Card */}
        <div className="bg-card/50 backdrop-blur-xl border border-border/50 rounded-2xl p-8 shadow-2xl glass-effect">
          <div className="space-y-6">
            <form onSubmit={handleEmailSignup} className="space-y-5">
              <div className="space-y-4">
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Display Name"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="pl-10 bg-background/80 border-border/50 focus:border-primary/50 focus:ring-primary/20 rounded-xl h-12 transition-all duration-200"
                  />
                </div>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="email"
                    placeholder="Email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 bg-background/80 border-border/50 focus:border-primary/50 focus:ring-primary/20 rounded-xl h-12 transition-all duration-200"
                    required
                  />
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 bg-background/80 border-border/50 focus:border-primary/50 focus:ring-primary/20 rounded-xl h-12 transition-all duration-200"
                    required
                  />
                </div>
              </div>
              
              {error && (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm animate-slide-up">
                  {error}
                </div>
              )}
              
              <Button 
                type="submit" 
                className="w-full gradient-primary hover:opacity-90 h-12 rounded-xl shadow-lg shadow-primary/20 transition-all duration-200 font-medium text-base" 
                disabled={loading}
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Creating account...
                  </div>
                ) : (
                  'Sign up'
                )}
              </Button>
            </form>

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border/50" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card/50 px-4 text-muted-foreground">Or continue with</span>
              </div>
            </div>

            {/* Google Sign Up - only show if using Firebase auth */}
            {(isDevMode || isBackendAuth) ? (
              <div className="p-3 rounded-lg bg-muted/50 border border-border/50 text-sm text-muted-foreground text-center">
                Sign up with email and password above.
              </div>
            ) : (
              <Button
                type="button"
                variant="outline"
                className="w-full h-12 rounded-xl border-border/50 hover:bg-accent/50 hover:border-primary/30 transition-all duration-200 font-medium"
                onClick={handleGoogleSignup}
                disabled={loading}
              >
                <Chrome className="h-5 w-5 mr-2" />
                Continue with Google
              </Button>
            )}

            {/* Sign In Link */}
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to="/login" className="text-primary hover:text-primary/80 font-medium transition-colors">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Features */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-4 rounded-xl bg-card/30 border border-border/30 backdrop-blur-sm">
            <BarChart3 className="h-5 w-5 mx-auto mb-2 text-primary" />
            <p className="text-xs text-muted-foreground">Data Expert</p>
          </div>
          <div className="p-4 rounded-xl bg-card/30 border border-border/30 backdrop-blur-sm">
            <Lock className="h-5 w-5 mx-auto mb-2 text-primary" />
            <p className="text-xs text-muted-foreground">Secure</p>
          </div>
          <div className="p-4 rounded-xl bg-card/30 border border-border/30 backdrop-blur-sm">
            <Database className="h-5 w-5 mx-auto mb-2 text-primary" />
            <p className="text-xs text-muted-foreground">ML Ready</p>
          </div>
        </div>
      </div>
    </div>
  )
}
