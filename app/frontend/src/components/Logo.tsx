import { BarChart3, Database } from 'lucide-react'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg'
  showIcon?: boolean
  className?: string
}

export default function Logo({ size = 'md', showIcon = true, className = '' }: LogoProps) {
  const sizeClasses = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-4xl',
  }

  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-8 w-8',
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {showIcon && (
        <div className="relative flex items-center">
          <Database className={`${iconSizes[size]} text-primary animate-pulse-slow`} />
          <BarChart3 className={`${iconSizes[size]} text-primary animate-pulse-slow -ml-2`} style={{ animationDelay: '0.5s' }} />
          <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
        </div>
      )}
      <span className={`font-bold ${sizeClasses[size]}`}>
        <span className="text-gradient">Dat</span>
        <span className="text-foreground">.</span>
        <span className="text-gradient">AI</span>
      </span>
    </div>
  )
}

