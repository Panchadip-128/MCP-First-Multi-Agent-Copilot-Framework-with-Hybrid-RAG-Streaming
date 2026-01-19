import { Outlet, Link, useLocation } from 'react-router-dom'
import { MessageSquare, Folder, Wrench, Github } from 'lucide-react'
import clsx from 'clsx'

export default function Layout() {
  const location = useLocation()
  
  const isActive = (path: string) => {
    return location.pathname === path
  }
  
  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            LLM Copilot
          </h1>
          <p className="text-sm text-gray-400 mt-1">Framework v0.1</p>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          <NavLink to="/" icon={<MessageSquare size={20} />} active={isActive('/')}>
            Home
          </NavLink>
          <NavLink to="/chat" icon={<MessageSquare size={20} />} active={isActive('/chat')}>
            Chat
          </NavLink>
          <NavLink to="/projects" icon={<Folder size={20} />} active={isActive('/projects')}>
            Projects
          </NavLink>
          <NavLink to="/tools" icon={<Wrench size={20} />} active={isActive('/tools')}>
            Tools
          </NavLink>
        </nav>
        
        {/* Footer */}
        <div className="p-4 border-t border-gray-700">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-gray-400 hover:text-gray-200 transition-colors"
          >
            <Github size={18} />
            <span className="text-sm">GitHub</span>
          </a>
        </div>
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

function NavLink({ 
  to, 
  icon, 
  active, 
  children 
}: { 
  to: string
  icon: React.ReactNode
  active: boolean
  children: React.ReactNode
}) {
  return (
    <Link
      to={to}
      className={clsx(
        'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
        active
          ? 'bg-blue-600 text-white'
          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
      )}
    >
      {icon}
      <span className="font-medium">{children}</span>
    </Link>
  )
}
