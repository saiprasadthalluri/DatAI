import Logo from './Logo'

export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-background via-background to-secondary/20 gradient-mesh">
      <div className="text-center space-y-6 animate-fade-in">
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
          <div className="relative animate-spin rounded-full h-16 w-16 border-4 border-primary/20 border-t-primary mx-auto" />
        </div>
        <Logo size="lg" />
        <p className="text-muted-foreground text-sm">Loading your data science expert...</p>
      </div>
    </div>
  )
}


