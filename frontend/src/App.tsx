import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { ThemeProvider } from './contexts/ThemeContext'
import { ChatProvider } from './contexts/ChatContext'
import { AuthProvider } from './contexts/AuthContext'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'
import LoginPage from './pages/LoginPage'
import DataSourcesPage from './pages/DataSourcesPage'
import AlertsPage from './pages/AlertsPage'
import GraphPage from './pages/GraphPage'
import ModelsPage from './pages/ModelsPage'
import AdminPage from './pages/AdminPage'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ChatProvider>
          <Router>
            <Routes>
              {/* Rota pública de login */}
              <Route path="/login" element={<LoginPage />} />
              
              {/* Rotas protegidas */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route index element={<Navigate to="/chat" replace />} />
                <Route path="chat" element={<ChatPage />} />
                <Route path="sources" element={<DataSourcesPage />} />
                <Route path="analytics" element={<AnalyticsPage />} />
                <Route path="alerts" element={<AlertsPage />} />
                <Route path="graph" element={<GraphPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="models" element={<ModelsPage />} />
                <Route path="admin" element={<AdminPage />} />
              </Route>
            </Routes>
          </Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3000,
              style: {
                background: 'var(--toast-bg)',
                color: 'var(--toast-color)',
              },
            }}
          />
        </ChatProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
