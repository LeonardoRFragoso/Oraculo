import { useEffect, useState } from 'react'
import { Settings, Database, Brain, Shield, RefreshCw, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

interface HealthData {
  status: string
  version: string
  environment: string
  uptime_seconds: number
  checks: Record<string, boolean>
  details: {
    llm: { available: boolean; provider: string; anthropic_key_set: boolean; openai_key_set: boolean; opencode_key_set: boolean; zai_key_set: boolean }
    vector_store: { available: boolean; backend: string; indexed_sources: number }
    database: { available: boolean; backend: string }
    catalog: { available: boolean; total_sources: number; connected_sources: number }
    auth: { secret_key_set: boolean; require_auth: boolean }
  }
}

function StatusBadge({ ok, label }: { ok: boolean; label?: string }) {
  if (ok) {
    return (
      <span className="flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
        <CheckCircle className="w-3.5 h-3.5" /> {label || 'Online'}
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
      <XCircle className="w-3.5 h-3.5" /> {label || 'Offline'}
    </span>
  )
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('access_token')
      const resp = await axios.get(`${API_BASE}/health`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      setHealth(resp.data)
      setLastUpdated(new Date())
    } catch (e: any) {
      setError('Não foi possível conectar ao backend.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchHealth() }, [])

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold gradient-text">Configurações</h1>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 mb-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
            <AlertCircle className="w-5 h-5" /> {error}
          </div>
        )}

        {lastUpdated && (
          <p className="text-xs text-gray-400 mb-4">
            Atualizado: {lastUpdated.toLocaleTimeString('pt-BR')}
          </p>
        )}

        <div className="space-y-6">
          {/* Status Geral */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Settings className="w-6 h-6 text-primary" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Sistema</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {[
                { label: 'Versão', value: health?.version ?? '—' },
                { label: 'Ambiente', value: health?.environment ?? '—' },
                { label: 'Uptime', value: health ? formatUptime(health.uptime_seconds) : '—' },
                { label: 'Status', value: health?.status === 'healthy' ? '✅ Saudável' : health?.status === 'degraded' ? '⚠️ Degradado' : '—' },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                  <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                  <p className="font-semibold text-gray-900 dark:text-gray-100 mt-0.5">{value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* IA / LLM */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Brain className="w-6 h-6 text-purple-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Inteligência Artificial</h2>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">LLM Provider</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {health?.details.llm.provider ? `Provedor ativo: ${health.details.llm.provider}` : 'Nenhum provedor configurado'}
                  </p>
                </div>
                <StatusBadge ok={health?.details.llm.available ?? false} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Anthropic API Key</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Claude Haiku / Sonnet</p>
                </div>
                <StatusBadge ok={health?.details.llm.anthropic_key_set ?? false} label={health?.details.llm.anthropic_key_set ? 'Configurada' : 'Não configurada'} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">OpenAI API Key</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">GPT-4o / text-embedding</p>
                </div>
                <StatusBadge ok={health?.details.llm.openai_key_set ?? false} label={health?.details.llm.openai_key_set ? 'Configurada' : 'Não configurada'} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">OpenCode Zen API Key</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Modelos gratuitos e pagos</p>
                </div>
                <StatusBadge ok={health?.details.llm.opencode_key_set ?? false} label={health?.details.llm.opencode_key_set ? 'Configurada' : 'Não configurada'} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Z.AI API Key</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">GLM-4.5 / GLM-5</p>
                </div>
                <StatusBadge ok={health?.details.llm.zai_key_set ?? false} label={health?.details.llm.zai_key_set ? 'Configurada' : 'Não configurada'} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Vector Store</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {health?.details.vector_store.backend ?? 'faiss'} — {health?.details.vector_store.indexed_sources ?? 0} fonte(s) indexada(s)
                  </p>
                </div>
                <StatusBadge ok={health?.details.vector_store.available ?? false} />
              </div>
            </div>
          </div>

          {/* Dados */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Database className="w-6 h-6 text-blue-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Dados</h2>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Banco de Dados</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Backend: {health?.details.database.backend ?? '—'}
                  </p>
                </div>
                <StatusBadge ok={health?.details.database.available ?? false} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Catálogo de Fontes</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {health?.details.catalog.total_sources ?? 0} total — {health?.details.catalog.connected_sources ?? 0} conectada(s)
                  </p>
                </div>
                <StatusBadge ok={health?.details.catalog.available ?? false} />
              </div>
            </div>
          </div>

          {/* Segurança */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-6 h-6 text-green-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Segurança</h2>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Autenticação JWT</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {health?.details.auth.require_auth ? 'Obrigatória em todas as rotas' : 'Modo desenvolvimento (desativada)'}
                  </p>
                </div>
                <StatusBadge ok={health?.details.auth.require_auth ?? false} label={health?.details.auth.require_auth ? 'Ativa' : 'Desativada'} />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Secret Key</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Chave de assinatura JWT</p>
                </div>
                <StatusBadge ok={health?.details.auth.secret_key_set ?? false} label={health?.details.auth.secret_key_set ? 'Configurada' : 'Efêmera'} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
