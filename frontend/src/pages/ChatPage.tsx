import { useRef, useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Send, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [useStreaming, setUseStreaming] = useState<boolean>(true)
  const [isStreaming, setIsStreaming] = useState<boolean>(false)
  const isSendingRef = useRef(false)
  const streamControllerRef = useRef<AbortController | null>(null)
  
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: api.getProjects,
  })
  
  const chatMutation = useMutation({
    mutationFn: api.sendChatMessage,
    onSuccess: (data) => {
      setMessages(prev => [...prev, data.message])
    },
  })
  
  const handleSend = () => {
    if (!input.trim() || isStreaming || isSendingRef.current) return
    
    const userMessage: Message = {
      role: 'user',
      content: input,
    }
    
    setMessages(prev => [...prev, userMessage])
    setInput('')

    const payload = {
      messages: [...messages, userMessage],
      project_id: selectedProject || undefined,
      use_memory: !!selectedProject,
    }

    if (!useStreaming) {
      chatMutation.mutate(payload)
      return
    }

    // Streaming mode (SSE)
    isSendingRef.current = true
    setIsStreaming(true)
    const assistantIndex = messages.length + 1
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    // Abort any previous stream
    if (streamControllerRef.current) {
      streamControllerRef.current.abort()
    }
    const controller = new AbortController()
    streamControllerRef.current = controller

    fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    }).then(async (res) => {
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) throw new Error('No stream reader')

      let buffer = ''
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''
        for (const part of parts) {
          const lines = part.split('\n').filter(l => l.startsWith('data:'))
          for (const l of lines) {
            const data = l.replace(/^data:\s?/, '')
            if (!data) continue
            if (data === '[DONE]') {
              setIsStreaming(false)
              isSendingRef.current = false
              return
            }
            if (data.startsWith('[ERROR]')) {
              setIsStreaming(false)
              isSendingRef.current = false
              return
            }

            setMessages(prev => {
              const next = [...prev]
              const target = next[assistantIndex]
              if (target && target.role === 'assistant') {
                // De-duplicate adjacent repeated tokens
                const append = target.content.endsWith(data) ? '' : data
                target.content += append
                next[assistantIndex] = { ...target }
              }
              return next
            })
          }
        }
      }
      setIsStreaming(false)
      isSendingRef.current = false
    }).catch(() => {
      setIsStreaming(false)
      isSendingRef.current = false
    })
  }
  
  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <h1 className="text-2xl font-bold">Chat</h1>
          <div className="flex items-center gap-4">
            <label className="text-sm text-gray-400">Project:</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
            >
              <option value="">No project (general chat)</option>
              {projects?.map((project: any) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={useStreaming}
                onChange={(e) => setUseStreaming(e.target.checked)}
              />
              Stream
            </label>
          </div>
        </div>
      </header>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 mt-20">
              <p className="text-lg mb-2">Start a conversation</p>
              <p className="text-sm">
                {selectedProject 
                  ? 'Context-aware chat with RAG memory enabled' 
                  : 'General chat mode - select a project for code context'}
              </p>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} message={msg} />
          ))}
          
          {(chatMutation.isPending || isStreaming) && (
            <div className="flex justify-start">
              <div className="bg-gray-800 rounded-lg p-4 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-gray-400">Thinking...</span>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Input */}
      <div className="bg-gray-800 border-t border-gray-700 p-4">
        <div className="max-w-4xl mx-auto flex gap-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder="Ask anything about your code..."
            className="flex-1 bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-blue-500"
            disabled={chatMutation.isPending || isStreaming}
          />
          <button
            onClick={handleSend}
            disabled={chatMutation.isPending || isStreaming || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg transition-colors flex items-center gap-2"
          >
            <Send size={18} />
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-lg p-4 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-800 text-gray-100 border border-gray-700'
        }`}
      >
        <div className="text-sm font-semibold mb-2 opacity-75">
          {isUser ? 'You' : 'Assistant'}
        </div>
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>
    </div>
  )
}
