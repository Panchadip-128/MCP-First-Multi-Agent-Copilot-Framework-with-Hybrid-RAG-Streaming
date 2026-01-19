import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Wrench, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

type ToolSpec = {
  name: string
  description: string
  parameters_schema: {
    properties?: Record<string, { type?: string; description?: string }>
    required?: string[]
  }
}

export default function ToolsPage() {
  const { data: toolSpecs, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['tool-specs'],
    queryFn: api.getToolSpecs,
  })

  const [goal, setGoal] = useState('')
  const [planResult, setPlanResult] = useState<string | null>(null)
  const [planError, setPlanError] = useState<string | null>(null)

  const planMutation = useMutation({
    mutationFn: api.planTool,
    onSuccess: (data) => {
      setPlanResult(JSON.stringify(data, null, 2))
      setPlanError(null)
    },
    onError: (err: any) => {
      setPlanError(err?.message || 'Planner failed')
      setPlanResult(null)
    },
  })

  const [agentGoal, setAgentGoal] = useState('')
  const [agentResult, setAgentResult] = useState<string | null>(null)
  const [agentError, setAgentError] = useState<string | null>(null)

  const agentMutation = useMutation({
    mutationFn: api.runMultiAgent,
    onSuccess: (data) => {
      setAgentResult(JSON.stringify(data, null, 2))
      setAgentError(null)
    },
    onError: (err: any) => {
      setAgentError(err?.message || 'Multi-agent run failed')
      setAgentResult(null)
    },
  })

  const [workflowGoal, setWorkflowGoal] = useState('')
  const [workflowResult, setWorkflowResult] = useState<string | null>(null)
  const [workflowError, setWorkflowError] = useState<string | null>(null)

  const workflowMutation = useMutation({
    mutationFn: api.runWorkflow,
    onSuccess: (data) => {
      setWorkflowResult(JSON.stringify(data, null, 2))
      setWorkflowError(null)
    },
    onError: (err: any) => {
      setWorkflowError(err?.message || 'Workflow run failed')
      setWorkflowResult(null)
    },
  })

  const { data: plugins } = useQuery({
    queryKey: ['plugins'],
    queryFn: api.getPlugins,
  })

  const reloadPluginsMutation = useMutation({
    mutationFn: api.reloadPlugins,
  })
  
  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Tools & Agents</h1>
          <p className="text-gray-400">
            Available tools for code execution, debugging, and analysis
          </p>
        </div>

        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-2">Planner (Agent Orchestration)</h2>
          <p className="text-gray-400 text-sm mb-4">
            Describe a goal. The planner selects and runs the best tool.
          </p>
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Example: Find where MCPProtocol is defined and show its first 20 lines"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white min-h-[100px]"
          />
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={() => planMutation.mutate({ goal })}
              disabled={planMutation.isPending || !goal.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded text-sm"
            >
              {planMutation.isPending ? 'Planning...' : 'Run Planner'}
            </button>
            <button
              onClick={() => {
                setGoal('')
                setPlanResult(null)
                setPlanError(null)
              }}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm"
            >
              Reset
            </button>
          </div>

          {planError && (
            <div className="text-red-400 text-sm mt-3">{planError}</div>
          )}

          {planResult && (
            <pre className="bg-gray-900 border border-gray-700 rounded p-3 text-sm text-gray-200 overflow-x-auto mt-3">
{planResult}
            </pre>
          )}
        </div>

        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-2">Multi-Agent Run (Planner → Coder → Reviewer → Tester)</h2>
          <p className="text-gray-400 text-sm mb-4">
            Run a full multi-agent workflow and get plan, implementation, review, and tests.
          </p>
          <textarea
            value={agentGoal}
            onChange={(e) => setAgentGoal(e.target.value)}
            placeholder="Example: Add a new endpoint to list tools with schemas"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white min-h-[100px]"
          />
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={() => agentMutation.mutate({ goal: agentGoal })}
              disabled={agentMutation.isPending || !agentGoal.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded text-sm"
            >
              {agentMutation.isPending ? 'Running...' : 'Run Multi-Agent'}
            </button>
            <button
              onClick={() => {
                setAgentGoal('')
                setAgentResult(null)
                setAgentError(null)
              }}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm"
            >
              Reset
            </button>
          </div>

          {agentError && (
            <div className="text-red-400 text-sm mt-3">{agentError}</div>
          )}

          {agentResult && (
            <pre className="bg-gray-900 border border-gray-700 rounded p-3 text-sm text-gray-200 overflow-x-auto mt-3">
{agentResult}
            </pre>
          )}
        </div>

        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-2">Industry Workflow (Trace + Tools + Review)</h2>
          <p className="text-gray-400 text-sm mb-4">
            Runs planning, optional tool execution, coding, review, and tests with a full trace.
          </p>
          <textarea
            value={workflowGoal}
            onChange={(e) => setWorkflowGoal(e.target.value)}
            placeholder="Example: Add a new endpoint to list tools with schemas and document it"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white min-h-[100px]"
          />
          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={() => workflowMutation.mutate({ goal: workflowGoal, run_tools: true })}
              disabled={workflowMutation.isPending || !workflowGoal.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded text-sm"
            >
              {workflowMutation.isPending ? 'Running...' : 'Run Workflow'}
            </button>
            <button
              onClick={() => {
                setWorkflowGoal('')
                setWorkflowResult(null)
                setWorkflowError(null)
              }}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm"
            >
              Reset
            </button>
          </div>

          {workflowError && (
            <div className="text-red-400 text-sm mt-3">{workflowError}</div>
          )}

          {workflowResult && (
            <pre className="bg-gray-900 border border-gray-700 rounded p-3 text-sm text-gray-200 overflow-x-auto mt-3">
{workflowResult}
            </pre>
          )}
        </div>

        <div className="mb-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xl font-semibold">Plugins</h2>
            <button
              onClick={() => reloadPluginsMutation.mutate()}
              className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1 rounded text-sm"
            >
              Reload
            </button>
          </div>
          <p className="text-gray-400 text-sm mb-4">
            Loaded plugin manifests and tools.
          </p>

          {!plugins || plugins.length === 0 ? (
            <div className="text-gray-400 text-sm">No plugins loaded.</div>
          ) : (
            <div className="space-y-3">
              {plugins.map((p: any, idx: number) => (
                <div key={idx} className="bg-gray-900 border border-gray-700 rounded p-3">
                  <div className="text-white font-semibold">{p.name}</div>
                  <div className="text-gray-400 text-sm">{p.description}</div>
                  <div className="text-gray-500 text-xs">v{p.version}</div>
                  <div className="mt-2 text-gray-300 text-sm">
                    Tools: {(p.tools || []).map((t: any) => t.name).join(', ')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : isError ? (
          <div className="bg-gray-800 rounded-lg p-6 border border-red-700">
            <div className="text-red-400 text-sm mb-3">
              Failed to load tools: {(error as any)?.message || 'Unknown error'}
            </div>
            <button
              onClick={() => refetch()}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm"
            >
              Retry
            </button>
          </div>
        ) : toolSpecs && toolSpecs.length > 0 ? (
          <div className="grid gap-4">
            {toolSpecs.map((spec: ToolSpec) => (
              <ToolCard key={spec.name} spec={spec} />
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-400 py-20">
            <Wrench className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg mb-2">No tools registered yet</p>
            <p className="text-sm">Tools will appear here once registered with MCP</p>
          </div>
        )}
      </div>
    </div>
  )
}

function ToolCard({ spec }: { spec: ToolSpec }) {
  const [expanded, setExpanded] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const properties = spec.parameters_schema?.properties || {}
  const initialParams = Object.keys(properties).reduce<Record<string, string>>(
    (acc, key) => {
      acc[key] = ''
      return acc
    },
    {},
  )
  const [params, setParams] = useState<Record<string, string>>(initialParams)

  const executeMutation = useMutation({
    mutationFn: api.executeTool,
    onSuccess: (data) => {
      setResult(JSON.stringify(data, null, 2))
      setError(null)
    },
    onError: (err: any) => {
      setError(err?.message || 'Tool execution failed')
      setResult(null)
    },
  })

  const handleExecute = () => {
    setResult(null)
    setError(null)

    const typedParams: Record<string, any> = {}
    for (const [key, value] of Object.entries(params)) {
      const type = properties[key]?.type || 'string'
      if (type === 'number' || type === 'integer') {
        typedParams[key] = Number(value)
      } else if (type === 'boolean') {
        typedParams[key] = value === 'true'
      } else {
        typedParams[key] = value
      }
    }

    executeMutation.mutate({
      tool_name: spec.name,
      parameters: typedParams,
    })
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
          <Wrench className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold">{spec.name}</h3>
          <p className="text-gray-400 text-sm">{spec.description}</p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded transition-colors text-sm"
        >
          {expanded ? 'Close' : 'Execute'}
        </button>
      </div>

      {expanded && (
        <div className="mt-6 space-y-4">
          {Object.keys(properties).length === 0 ? (
            <div className="text-gray-400 text-sm">No parameters required.</div>
          ) : (
            Object.entries(properties).map(([key, schema]) => (
              <div key={key}>
                <label className="block text-sm text-gray-300 mb-1">{key}</label>
                <input
                  value={params[key] || ''}
                  onChange={(e) => setParams({ ...params, [key]: e.target.value })}
                  className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-white"
                  placeholder={schema.description || `Enter ${key}`}
                />
              </div>
            ))
          )}

          <div className="flex items-center gap-3">
            <button
              onClick={handleExecute}
              disabled={executeMutation.isPending}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded transition-colors text-sm"
            >
              {executeMutation.isPending ? 'Running...' : 'Run'}
            </button>
            <button
              onClick={() => {
                setParams(initialParams)
                setResult(null)
                setError(null)
              }}
              className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded transition-colors text-sm"
            >
              Reset
            </button>
          </div>

          {error && (
            <div className="text-red-400 text-sm">{error}</div>
          )}

          {result && (
            <pre className="bg-gray-900 border border-gray-700 rounded p-3 text-sm text-gray-200 overflow-x-auto">
{result}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
