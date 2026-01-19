import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Folder, Plus, Trash2, Upload } from 'lucide-react'
import { api } from '@/lib/api'

export default function ProjectsPage() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const queryClient = useQueryClient()
  
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: api.getProjects,
  })
  
  const deleteMutation = useMutation({
    mutationFn: api.deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
  
  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Projects</h1>
            <p className="text-gray-400">
              Manage your code projects and RAG memory indices
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus size={20} />
            New Project
          </button>
        </div>
        
        {/* Projects Grid */}
        {isLoading ? (
          <div className="text-center text-gray-400 py-20">Loading projects...</div>
        ) : projects && projects.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project: any) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={() => deleteMutation.mutate(project.id)}
              />
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-400 py-20">
            <Folder className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg mb-2">No projects yet</p>
            <p className="text-sm">Create your first project to get started</p>
          </div>
        )}
      </div>
      
      {showCreateModal && (
        <CreateProjectModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  )
}

function ProjectCard({ 
  project, 
  onDelete 
}: { 
  project: any
  onDelete: () => void
}) {
  const [showUpload, setShowUpload] = useState(false)
  
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <Folder className="w-8 h-8 text-blue-400" />
          <div>
            <h3 className="font-semibold text-lg">{project.name}</h3>
            <span className="text-sm text-gray-400">{project.language}</span>
          </div>
        </div>
        <button
          onClick={onDelete}
          className="text-gray-400 hover:text-red-400 transition-colors"
        >
          <Trash2 size={18} />
        </button>
      </div>
      
      {project.description && (
        <p className="text-gray-400 text-sm mb-4">{project.description}</p>
      )}
      
      <div className="flex gap-2">
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm flex items-center justify-center gap-2 transition-colors"
        >
          <Upload size={16} />
          Upload Code
        </button>
      </div>
      
      {showUpload && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          <FileUpload projectId={project.id} />
        </div>
      )}
    </div>
  )
}

function CreateProjectModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [language, setLanguage] = useState('python')
  const queryClient = useQueryClient()
  
  const createMutation = useMutation({
    mutationFn: api.createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      onClose()
    },
  })
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate({ name, description, language })
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full border border-gray-700">
        <h2 className="text-2xl font-bold mb-4">Create New Project</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Project Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-700 text-white px-4 py-2 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-gray-700 text-white px-4 py-2 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
              rows={3}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full bg-gray-700 text-white px-4 py-2 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
            </select>
          </div>
          
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded transition-colors"
            >
              {createMutation.isPending ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function FileUpload({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient()
  
  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadFile(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadMutation.mutate(file)
    }
  }
  
  return (
    <div>
      <input
        type="file"
        onChange={handleFileChange}
        accept=".py,.js,.ts,.java,.cpp,.c,.h,.hpp,.go,.rs,.rb,.php"
        className="text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700 file:cursor-pointer"
      />
      {uploadMutation.isPending && (
        <p className="text-sm text-gray-400 mt-2">Indexing...</p>
      )}
      {uploadMutation.isSuccess && (
        <p className="text-sm text-green-400 mt-2">✓ Indexed successfully</p>
      )}
    </div>
  )
}
