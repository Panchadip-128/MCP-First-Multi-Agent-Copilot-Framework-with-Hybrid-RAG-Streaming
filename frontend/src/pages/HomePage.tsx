import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Sparkles, Zap, Code, Database } from 'lucide-react'
import { api } from '@/lib/api'

export default function HomePage() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
  })
  
  return (
    <div className="p-8">
      {/* Header */}
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
            LLM Copilot Framework
          </h1>
          <p className="text-xl text-gray-400">
            Open-source modular framework for AI-powered developer copilots
          </p>
          <div className="mt-6 flex items-center justify-center gap-4">
            <StatusBadge 
              label="API Status" 
              status={health?.status || 'unknown'} 
            />
            <StatusBadge 
              label="Version" 
              status={health?.version || '0.1.0'} 
              variant="neutral"
            />
          </div>
        </div>
        
        {/* Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <FeatureCard
            icon={<Sparkles className="w-8 h-8 text-blue-400" />}
            title="MCP Protocol"
            description="Standardized message passing between LLM, tools, and agents"
          />
          <FeatureCard
            icon={<Database className="w-8 h-8 text-purple-400" />}
            title="RAG Memory"
            description="Vector-based codebase indexing with semantic search"
          />
          <FeatureCard
            icon={<Code className="w-8 h-8 text-green-400" />}
            title="Tool Agents"
            description="Code execution, debugging, testing, and refactoring"
          />
          <FeatureCard
            icon={<Zap className="w-8 h-8 text-yellow-400" />}
            title="LLM Router"
            description="Multi-model support with intelligent task-based routing"
          />
        </div>
        
        {/* Quick Start */}
        <div className="bg-gray-800 rounded-lg p-8 border border-gray-700">
          <h2 className="text-2xl font-bold mb-4">Quick Start</h2>
          <div className="space-y-4 text-gray-300">
            <Step number={1}>
              Create a new project in the <Link to="/projects">Projects</Link> page
            </Step>
            <Step number={2}>
              Upload your codebase files to build the RAG memory index
            </Step>
            <Step number={3}>
              Start chatting in the <Link to="/chat">Chat</Link> page with full context awareness
            </Step>
            <Step number={4}>
              Use <Link to="/tools">Tools</Link> for code execution, debugging, and more
            </Step>
          </div>
        </div>
        
        {/* Architecture */}
        <div className="mt-12 bg-gray-800 rounded-lg p-8 border border-gray-700">
          <h2 className="text-2xl font-bold mb-4">System Architecture</h2>
          <pre className="bg-gray-900 p-6 rounded-lg text-sm text-gray-300 overflow-x-auto">
{`┌─────────────────────────────────────────────────────────────┐
│                      Frontend Extension                      │
│         (React + Monaco Editor + Chat Interface)            │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      MCP Protocol Layer                      │
│          (Message routing, tool calling, state mgmt)        │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────┬──────────────┬──────────────┬────────────────┐
│  LLM Router  │  RAG Memory  │ Tool Agents  │ Plugin Manager │
│  (Multi-LLM) │  (Vector DB) │ (Executors)  │  (Extensions)  │
└──────────────┴──────────────┴──────────────┴────────────────┘`}
          </pre>
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ 
  label, 
  status, 
  variant = 'success' 
}: { 
  label: string
  status: string
  variant?: 'success' | 'neutral'
}) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-full border border-gray-700">
      <span className="text-sm text-gray-400">{label}:</span>
      <span className={variant === 'success' ? 'text-green-400' : 'text-gray-300'}>
        {status}
      </span>
    </div>
  )
}

function FeatureCard({ 
  icon, 
  title, 
  description 
}: { 
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
    </div>
  )
}

function Step({ 
  number, 
  children 
}: { 
  number: number
  children: React.ReactNode
}) {
  return (
    <div className="flex gap-4">
      <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center font-bold">
        {number}
      </div>
      <div className="flex-1 pt-1">{children}</div>
    </div>
  )
}
