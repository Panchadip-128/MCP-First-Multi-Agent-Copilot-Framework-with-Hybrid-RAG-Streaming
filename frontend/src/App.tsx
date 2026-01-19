import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import ChatPage from './pages/ChatPage'
import ProjectsPage from './pages/ProjectsPage'
import ToolsPage from './pages/ToolsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="tools" element={<ToolsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
