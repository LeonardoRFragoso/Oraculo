import { Link, useNavigate } from 'react-router-dom'
import { Moon, Sun, Settings, Sparkles, LogOut, User, Zap, Crown } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'

const PLAN_BADGES: Record<string, { icon: typeof Sparkles; label: string; classes: string }> = {
  free: { icon: Sparkles, label: 'Free', classes: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' },
  premium: { icon: Zap, label: 'Premium', classes: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' },
  enterprise: { icon: Crown, label: 'Enterprise', classes: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400' },
}

export default function Header() {
  const { theme, toggleTheme } = useTheme()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="bg-white dark:bg-dark-surface border-b border-light-border dark:border-dark-border">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text">ORÁCULO</h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">Insights que Antecipam o Futuro</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          {/* User Info */}
          {user && (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800">
                <User className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {user.full_name || user.username}
                </span>
              </div>
              {(() => {
                const plan = user.plan || 'free'
                const badge = PLAN_BADGES[plan] || PLAN_BADGES.free
                const PlanIcon = badge.icon
                if (plan === 'enterprise') {
                  return (
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold ${badge.classes}`}>
                      <PlanIcon className="w-3.5 h-3.5" /> {badge.label}
                    </span>
                  )
                }
                return (
                  <Link
                    to="/pricing"
                    className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold ${badge.classes} hover:opacity-80 transition-opacity`}
                    title="Fazer upgrade"
                  >
                    <PlanIcon className="w-3.5 h-3.5" /> {badge.label}
                  </Link>
                )
              })()}
            </div>
          )}

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            ) : (
              <Moon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            )}
          </button>

          {/* Settings */}
          <Link
            to="/settings"
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </Link>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors"
            aria-label="Logout"
            title="Sair"
          >
            <LogOut className="w-5 h-5 text-red-600 dark:text-red-400" />
          </button>
        </div>
      </div>
    </header>
  )
}
