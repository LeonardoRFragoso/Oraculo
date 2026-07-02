import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Crown, Zap, Sparkles, RotateCcw, Users, Shield } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../contexts/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

interface UserItem {
  id: string
  username: string
  email: string | null
  full_name: string | null
  is_active: boolean
  is_admin: boolean
  plan: string
  plan_expires_at: string | null
  llm_quota_monthly: number
  llm_quota_used: number
  created_at: string
}

const PLAN_ICONS: Record<string, typeof Sparkles> = {
  free: Sparkles,
  premium: Zap,
  enterprise: Crown,
}

const PLAN_COLORS: Record<string, string> = {
  free: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  premium: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  enterprise: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
}

function getAuthHeaders() {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function AdminPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [users, setUsers] = useState<UserItem[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<string | null>(null)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await axios.get(`${API_BASE}/auth/users`, { headers: getAuthHeaders() })
      setUsers(resp.data.users || [])
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      toast.error(detail || 'Erro ao carregar usuários.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!user?.is_admin) {
      toast.error('Acesso negado. Apenas administradores.')
      navigate('/chat')
      return
    }
    fetchUsers()
  }, [user, navigate])

  const handleUpdatePlan = async (username: string, plan: string) => {
    setUpdating(username)
    try {
      await axios.put(
        `${API_BASE}/auth/users/${username}/plan`,
        { plan },
        { headers: getAuthHeaders() },
      )
      toast.success(`Plano de '${username}' atualizado para '${plan}'`)
      fetchUsers()
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      toast.error(detail || 'Erro ao atualizar plano.')
    } finally {
      setUpdating(null)
    }
  }

  const handleResetQuota = async (username: string) => {
    setUpdating(username)
    try {
      await axios.post(
        `${API_BASE}/auth/users/${username}/quota/reset`,
        {},
        { headers: getAuthHeaders() },
      )
      toast.success(`Quota de '${username}' resetada.`)
      fetchUsers()
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      toast.error(detail || 'Erro ao resetar quota.')
    } finally {
      setUpdating(null)
    }
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/settings')}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label="Voltar"
        >
          <ArrowLeft className="w-6 h-6 text-gray-600 dark:text-gray-400" />
        </button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold gradient-text">Administração</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Gerencie planos e cotas de LLM dos usuários.
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">
          <Shield className="w-4 h-4" />
          Admin
        </span>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-1">
            <Users className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-500 dark:text-gray-400">Total</span>
          </div>
          <div className="text-2xl font-bold">{users.length}</div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4 text-green-500" />
            <span className="text-sm text-gray-500 dark:text-gray-400">Free</span>
          </div>
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {users.filter(u => u.plan === 'free').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-gray-500 dark:text-gray-400">Premium</span>
          </div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {users.filter(u => u.plan === 'premium').length}
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-1">
            <Crown className="w-4 h-4 text-purple-500" />
            <span className="text-sm text-gray-500 dark:text-gray-400">Enterprise</span>
          </div>
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {users.filter(u => u.plan === 'enterprise').length}
          </div>
        </div>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">Usuário</th>
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">Plano</th>
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">Quota</th>
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">Role</th>
                  <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">Ações</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const PlanIcon = PLAN_ICONS[u.plan] || Sparkles
                  const planColor = PLAN_COLORS[u.plan] || PLAN_COLORS.free
                  const quotaPct = u.llm_quota_monthly > 0
                    ? Math.round((u.llm_quota_used / u.llm_quota_monthly) * 100)
                    : 0
                  const isUpdating = updating === u.username

                  return (
                    <tr
                      key={u.id}
                      className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="flex flex-col">
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {u.username}
                          </span>
                          {u.email && (
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {u.email}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${planColor}`}>
                            <PlanIcon className="w-3 h-3" />
                            {u.plan}
                          </span>
                        </div>
                        {isUpdating ? (
                          <div className="mt-1 w-20 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div className="h-full bg-primary animate-pulse rounded-full" style={{ width: '60%' }} />
                          </div>
                        ) : (
                          <select
                            value={u.plan}
                            onChange={(e) => handleUpdatePlan(u.username, e.target.value)}
                            disabled={isUpdating}
                            className="mt-1 text-xs bg-transparent border-none cursor-pointer text-gray-500 dark:text-gray-400 focus:outline-none focus:ring-0"
                          >
                            <option value="free">Free</option>
                            <option value="premium">Premium</option>
                            <option value="enterprise">Enterprise</option>
                          </select>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col gap-1">
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            {u.llm_quota_used} / {u.llm_quota_monthly}
                          </span>
                          <div className="w-24 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                quotaPct > 80 ? 'bg-red-500' : quotaPct > 50 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${Math.min(quotaPct, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {u.is_admin ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400">
                            <Shield className="w-3 h-3" /> Admin
                          </span>
                        ) : (
                          <span className="text-xs text-gray-500 dark:text-gray-400">User</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleResetQuota(u.username)}
                          disabled={isUpdating}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
                          title="Resetar quota"
                        >
                          <RotateCcw className="w-3 h-3" />
                          Reset
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && users.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          Nenhum usuário encontrado.
        </div>
      )}
    </div>
  )
}
