import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {
  return (
    <BrowserRouter>
      <div style={{ padding: '20px', color: 'white', background: '#1a1a1a', minHeight: '100vh' }}>
        <h1>Test Page - If you see this, React is working!</h1>
        <p>Frontend is running on port 3000</p>
        <p>Backend should be at port 8000</p>
      </div>
    </BrowserRouter>
  )
}

export default App
