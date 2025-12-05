import { useState } from 'react'

interface ModelSelectorProps {
  value: string
  onChange: (model: string) => void
  className?: string
}

const models = [
  { 
    id: 'auto', 
    label: '🤖 Auto (Smart Routing)', 
    description: 'Automatically picks the best specialist' 
  },
  { 
    id: 'theory-specialist', 
    label: '📚 Theory', 
    description: 'Data science concepts & ML theory' 
  },
  { 
    id: 'code-specialist', 
    label: '💻 Code', 
    description: 'Programming & debugging' 
  },
  { 
    id: 'math-specialist', 
    label: '🔢 Math', 
    description: 'Calculations & statistics' 
  },
]

export default function ModelSelector({ value, onChange, className = '' }: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  const selectedModel = models.find(m => m.id === value) || models[0]

  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-card/50 border border-border/50 hover:bg-card/70 transition-colors text-sm"
      >
        <span>{selectedModel.label}</span>
        <svg 
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 right-0 z-20 bg-card border border-border/50 rounded-xl shadow-lg overflow-hidden min-w-[200px]">
            {models.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => {
                  onChange(model.id)
                  setIsOpen(false)
                }}
                className={`w-full text-left px-4 py-3 hover:bg-accent/50 transition-colors ${
                  value === model.id ? 'bg-primary/10 border-l-2 border-primary' : ''
                }`}
              >
                <div className="font-medium text-sm">{model.label}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{model.description}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

