import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { auth } from '@/lib/firebase'
import { chatApi, conversationApi } from '@/lib/api'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Logo from '@/components/Logo'
import { Send, Plus, Settings, LogOut, BarChart3, Database, TrendingUp, Bot, User, Code2, MessageSquare, Trash2 } from 'lucide-react'
import ModelSelector from '@/components/ModelSelector'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export default function ChatPage() {
  const { conversationId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [message, setMessage] = useState('')
  const [selectedModel, setSelectedModel] = useState<'auto' | 'theory-specialist' | 'code-specialist' | 'math-specialist'>('auto')
  const [streamingMessage, setStreamingMessage] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch all conversations for history
  const { data: conversationsData } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => conversationApi.list({ limit: 50 }),
    refetchOnWindowFocus: false,
  })

  // Fetch conversation messages
  const { data: conversationData, error: conversationError } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => conversationApi.get(conversationId!),
    enabled: !!conversationId,
    retry: false, // Don't retry on 404
  })

  // Handle conversation not found - redirect to new chat
  useEffect(() => {
    if (conversationError && conversationId) {
      console.warn('Conversation not found, redirecting to new chat')
      navigate('/app', { replace: true })
    }
  }, [conversationError, conversationId, navigate])

  const sendMessageMutation = useMutation({
    mutationFn: chatApi.sendMessage,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversation', data.conversation_id] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      if (!conversationId) {
        navigate(`/app/c/${data.conversation_id}`)
      }
    },
  })

  const createConversationMutation = useMutation({
    mutationFn: () => conversationApi.create({ title: 'New Data Science Query' }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      navigate(`/app/c/${data.id}`)
    },
    onError: (error: any) => {
      console.error('Failed to create conversation:', error)
      alert('Failed to create new conversation. Please try again.')
    },
  })

  const deleteConversationMutation = useMutation({
    mutationFn: (id: string) => conversationApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      if (conversationId) {
        navigate('/app')
      }
    },
  })

  const handleDeleteConversation = (e: React.MouseEvent, convId: string) => {
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this conversation?')) {
      deleteConversationMutation.mutate(convId)
    }
  }

  const messages: Message[] = conversationData?.messages || []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || isStreaming) return

    const currentMessage = message
    setMessage('')
    setIsStreaming(true)
    setStreamingMessage('')

    // Use streaming by default
    try {
      // Check if user is authenticated
      const user = auth.getCurrentUser ? auth.getCurrentUser() : null
      if (!user) {
        alert('Please log in to send messages')
        setIsStreaming(false)
        return
      }
      
      console.log('Sending message:', { currentMessage, selectedModel, conversationId, user })
      
      await chatApi.sendMessageStream(
        {
          conversation_id: conversationId || undefined,
          message: currentMessage,
          meta: {
            model: selectedModel,
            mode: 'chat',  // Legacy, kept for compatibility
            temperature: 0.7,
            top_p: 0.95,
            max_tokens: 2048,
          },
        },
        {
          onMetadata: (metadata) => {
            console.log('Received metadata:', metadata)
            if (!conversationId && metadata.conversation_id) {
              queryClient.invalidateQueries({ queryKey: ['conversations'] })
              navigate(`/app/c/${metadata.conversation_id}`)
            }
          },
          onChunk: (chunk) => {
            console.log('Received chunk:', chunk)
            setStreamingMessage((prev) => prev + chunk)
          },
          onComplete: async (messageId) => {
            console.log('Stream complete:', messageId)
            setIsStreaming(false)
            setStreamingMessage('')
            // Invalidate queries to refresh conversation and list
            queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] })
            queryClient.invalidateQueries({ queryKey: ['conversations'] })
          },
          onError: (error) => {
            console.error('Streaming error:', error)
            console.error('Error details:', {
              message: error.message,
              stack: error.stack,
              name: error.name
            })
            setIsStreaming(false)
            setStreamingMessage('')
            // Show error to user
            alert(`Error: ${error.message || 'Failed to send message. Please try again.'}`)
            // Fallback to non-streaming
            try {
              sendMessageMutation.mutate({
                conversation_id: conversationId || undefined,
                message: currentMessage,
                meta: {
                  model: selectedModel,
                  mode: 'chat',  // Legacy, kept for compatibility
                  temperature: 0.7,
                  top_p: 0.95,
                  max_tokens: 2048,
                },
              })
            } catch (fallbackError) {
              console.error('Fallback error:', fallbackError)
            }
          },
        }
      )
    } catch (error: any) {
      console.error('Send message error:', error)
      setIsStreaming(false)
      setStreamingMessage('')
      alert(`Error: ${error.message || 'Failed to send message. Please check console for details.'}`)
    }
  }

  const handleNewChat = () => {
    createConversationMutation.mutate()
  }

  const handleLogout = async () => {
    await auth.signOut()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-background via-background to-secondary/20 gradient-mesh">
      {/* Sidebar */}
      <div className="w-72 border-r border-border/50 bg-card/50 backdrop-blur-xl flex flex-col shadow-2xl">
        {/* Logo Header - Sticky */}
        <div className="p-6 border-b border-border/50 sticky top-0 z-40 bg-card/50 backdrop-blur-xl">
          <Logo size="lg" />
          <p className="text-xs text-muted-foreground mt-2 ml-1">Your Data Science Expert</p>
        </div>

        {/* New Chat Button */}
        <div className="p-4 border-b border-border/50">
          <Button 
            onClick={handleNewChat} 
            className="w-full gradient-primary hover:opacity-90 transition-all duration-200 shadow-lg shadow-primary/20" 
            size="lg"
          >
            <Plus className="h-5 w-5 mr-2" />
            New Data Science Query
          </Button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 mb-2">
            Chat History
          </div>
          {conversationsData && conversationsData.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No conversations yet</p>
              <p className="text-xs mt-1">Start a new chat to begin</p>
            </div>
          )}
          {conversationsData && conversationsData.map((conv: any) => (
            <div
              key={conv.id}
              className={`group relative rounded-xl transition-all duration-200 ${
                conversationId === conv.id
                  ? 'bg-primary/20 border border-primary/30 shadow-lg shadow-primary/10'
                  : 'hover:bg-accent/50 border border-transparent'
              }`}
            >
              <button
                onClick={() => navigate(`/app/c/${conv.id}`)}
                className="w-full text-left p-3 pr-8"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg flex-shrink-0 ${
                    conversationId === conv.id ? 'bg-primary/20' : 'bg-muted/50'
                  }`}>
                    <MessageSquare className={`h-4 w-4 ${
                      conversationId === conv.id ? 'text-primary' : 'text-muted-foreground'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm truncate ${
                      conversationId === conv.id ? 'text-foreground font-medium' : 'text-muted-foreground'
                    }`}>
                      {conv.title || 'New Conversation'}
                    </p>
                    {conv.updated_at && (
                      <p className="text-xs text-muted-foreground/70 mt-0.5">
                        {new Date(conv.updated_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              </button>
              <button
                onClick={(e) => handleDeleteConversation(e, conv.id)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-destructive/20 text-muted-foreground hover:text-destructive transition-all"
                title="Delete conversation"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>

        {/* Bottom Actions */}
        <div className="p-4 border-t border-border/50 space-y-2 bg-card/30 mt-auto">
          <Button
            variant="ghost"
            className="w-full justify-start hover:bg-accent/50 transition-colors"
            onClick={() => navigate('/settings')}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          <Button 
            variant="ghost" 
            className="w-full justify-start hover:bg-destructive/10 hover:text-destructive transition-colors" 
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
        {/* Sticky Header - Always visible at top */}
        <div className="sticky top-0 z-50 bg-card/80 backdrop-blur-xl border-b border-border/50 shadow-sm">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <h2 className="text-lg font-semibold text-foreground">
                {conversationData?.title || 'New Conversation'}
              </h2>
              <ModelSelector value={selectedModel} onChange={setSelectedModel as (model: string) => void} />
            </div>
            <Logo size="md" className="flex-shrink-0" />
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md animate-fade-in">
                <div className="relative mb-6">
                  <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
                  <div className="relative z-10 flex items-center justify-center gap-2">
                    <Database className="h-16 w-16 text-primary animate-pulse-slow" />
                    <BarChart3 className="h-12 w-12 text-primary animate-pulse-slow" style={{ animationDelay: '0.5s' }} />
                  </div>
                </div>
                <h2 className="text-2xl font-bold mb-2 text-gradient">Welcome to Dat.AI</h2>
                <p className="text-muted-foreground mb-6">
                  Your expert data science assistant. Ask questions about data analysis, machine learning, statistics, and more.
                </p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-4 rounded-xl bg-card/50 border border-border/50 glass-effect">
                    <BarChart3 className="h-5 w-5 mb-2 text-primary" />
                    <p className="font-medium">Data Analysis</p>
                    <p className="text-xs text-muted-foreground">Get expert insights</p>
                  </div>
                  <div className="p-4 rounded-xl bg-card/50 border border-border/50 glass-effect">
                    <Code2 className="h-5 w-5 mb-2 text-primary" />
                    <p className="font-medium">ML & Stats</p>
                    <p className="text-xs text-muted-foreground">Code & algorithms</p>
                  </div>
                  <div className="p-4 rounded-xl bg-card/50 border border-border/50 glass-effect">
                    <Database className="h-5 w-5 mb-2 text-primary" />
                    <p className="font-medium">Data Science</p>
                    <p className="text-xs text-muted-foreground">Expert guidance</p>
                  </div>
                  <div className="p-4 rounded-xl bg-card/50 border border-border/50 glass-effect">
                    <TrendingUp className="h-5 w-5 mb-2 text-primary" />
                    <p className="font-medium">Visualizations</p>
                    <p className="text-xs text-muted-foreground">Charts & plots</p>
                  </div>
                </div>
                <div className="mt-6 space-y-2">
                  <p className="text-sm font-medium text-foreground text-center mb-3">Example questions:</p>
                  <div className="space-y-2">
                    <button
                      onClick={() => setMessage("How do I perform feature engineering?")}
                      className="w-full text-left p-3 rounded-lg bg-card/50 border border-border/50 hover:bg-card/70 hover:border-primary/30 transition-all text-sm text-muted-foreground hover:text-foreground"
                    >
                      💡 How do I perform feature engineering?
                    </button>
                    <button
                      onClick={() => setMessage("Explain random forests algorithm")}
                      className="w-full text-left p-3 rounded-lg bg-card/50 border border-border/50 hover:bg-card/70 hover:border-primary/30 transition-all text-sm text-muted-foreground hover:text-foreground"
                    >
                      🌲 Explain random forests algorithm
                    </button>
                    <button
                      onClick={() => setMessage("What's the best way to handle missing values in a dataset?")}
                      className="w-full text-left p-3 rounded-lg bg-card/50 border border-border/50 hover:bg-card/70 hover:border-primary/30 transition-all text-sm text-muted-foreground hover:text-foreground"
                    >
                      📊 Handle missing values in datasets
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {messages.map((msg, index) => (
            <div
              key={msg.id}
              className={`flex gap-4 animate-slide-up ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              {msg.role === 'assistant' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center shadow-lg shadow-primary/30">
                    <Bot className="h-4 w-4 text-white" />
                  </div>
                </div>
              )}
              <div
                className={`max-w-3xl rounded-2xl px-5 py-4 shadow-lg transition-all duration-200 ${
                  msg.role === 'user'
                    ? 'gradient-primary text-white rounded-br-sm'
                    : 'bg-card/80 border border-border/50 backdrop-blur-sm rounded-bl-sm'
                }`}
              >
                <div className="flex items-start gap-2">
                  {msg.role === 'user' && (
                    <User className="h-4 w-4 mt-0.5 flex-shrink-0 opacity-80" />
                  )}
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                </div>
              </div>
              {msg.role === 'user' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg">
                    <User className="h-4 w-4 text-white" />
                  </div>
                </div>
              )}
            </div>
          ))}
          {(sendMessageMutation.isPending || isStreaming) && (
            <div className="flex gap-4 justify-start animate-slide-up">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center shadow-lg shadow-primary/30">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              </div>
              <div className="bg-card/80 border border-border/50 backdrop-blur-sm rounded-2xl rounded-bl-sm px-5 py-4 shadow-lg max-w-3xl">
                {isStreaming && streamingMessage ? (
                  <p className="whitespace-pre-wrap leading-relaxed">{streamingMessage}</p>
                ) : (
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                  </div>
                )}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-border/50 bg-card/30 backdrop-blur-xl p-4">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ask a data science question... (e.g., 'How to handle missing values?')"
                  className="w-full bg-background/80 border-border/50 focus:border-primary/50 focus:ring-primary/20 rounded-xl px-4 py-3 pr-12 text-base backdrop-blur-sm transition-all duration-200"
                  disabled={sendMessageMutation.isPending || isStreaming}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSend(e)
                    }
                  }}
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                  Enter to send
                </div>
              </div>
              <Button 
                type="submit" 
                  disabled={sendMessageMutation.isPending || isStreaming || !message.trim()}
                className="gradient-primary hover:opacity-90 disabled:opacity-50 shadow-lg shadow-primary/20 px-6 h-12 rounded-xl transition-all duration-200"
              >
                {sendMessageMutation.isPending || isStreaming ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
