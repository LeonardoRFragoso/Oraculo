import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Cpu, Check, ArrowLeft, Sparkles, Crown, Zap, Gauge } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

interface Model {
  id: string
  name: string
  is_free: boolean
}

interface QuotaInfo {
  plan: string
  plan_label: string
  used: number
  monthly: number
  remaining: number
}

interface ActiveModelInfo {
  provider: string
  active_model: string | null
  plan: string
  scope: string
}

const PROVIDER_LABELS: Record<string, string> = {
  zai: 'Z.AI',
  opencode: 'OpenCode Zen',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
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

export default function ModelsPage() {
  const navigate = useNavigate()
  const [models, setModels] = useState<Model[]>([])
  const [activeModelInfo, setActiveModelInfo] = useState<ActiveModelInfo | null>(null)
  const [quota, setQuota] = useState<QuotaInfo | null>(null)
  const [availableProviders, setAvailableProviders] = useState<string[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string>('zai')
  const [loading, setLoading] = useState(true)
  const [selecting, setSelecting] = useState<string | null>(null)

  const fetchProvidersAndQuota = useCallback(async () => {
    try {
      const [providersResp, quotaResp, activeResp] = await Promise.all([
        axios.get(`${API_BASE}/models/providers`, { headers: getAuthHeaders() }),
        axios.get(`${API_BASE}/quota`, { headers: getAuthHeaders() }),
        axios.get(`${API_BASE}/active-model`, { headers: getAuthHeaders() }),
      ])
      setAvailableProviders(providersResp.data.providers || [])
      setQuota(quotaResp.data)
      setActiveModelInfo(activeResp.data)

      // Auto-select first available provider if current selection has no models
      const providers = providersResp.data.providers || []
      if (providers.length > 0 && !providers.includes(selectedProvider)) {
        setSelectedProvider(providers[0])
      }
    } catch (e) {
      // Non-fatal, continue with defaults
    }
  }, [selectedProvider])

  const fetchModels = useCallback(async () => {
    setLoading(true)
    try {
      const resp = await axios.get(
        `${API_BASE}/models?provider=${selectedProvider}`,
        { headers: getAuthHeaders() },
      )
      setModels(resp.data.models || [])
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      toast.error(detail || 'Erro ao carregar modelos.')
      setModels([])
    } finally {
      setLoading(false)
    }
  }, [selectedProvider])

  useEffect(() => {
    fetchProvidersAndQuota()
  }, [])

  useEffect(() => {
    fetchModels()
  }, [selectedProvider])

  const handleSelect = async (id: string) => {
    setSelecting(id)
    try {
      const resp = await axios.post(
        `${API_BASE}/active-model`,
        { model: id, provider: selectedProvider },
        { headers: getAuthHeaders() },
      )
      setActiveModelInfo({
        provider: resp.data.provider,
        active_model: resp.data.active_model,
        plan: resp.data.plan,
        scope: resp.data.scope,
      })
      toast.success(`Modelo ativo: ${id}`)
      // Refresh quota
      fetchProvidersAndQuota()
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      toast.error(detail || 'Erro ao selecionar modelo.')
    } finally {
      setSelecting(null)
    }
  }

  const planLabel = quota?.plan_label || activeModelInfo?.plan || 'Free'
  const planKey = (quota?.plan || activeModelInfo?.plan || 'free').toLowerCase()
  const PlanIcon = PLAN_ICONS[planKey] || Sparkles
  const planColor = PLAN_COLORS[planKey] || PLAN_COLORS.free
  const quotaPct = quota ? Math.round((quota.used / quota.monthly) * 100) : 0

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
          <h1 className="text-3xl font-bold gradient-text">Modelos de IA</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Selecione o modelo de LLM ativo para suas consultas.
          </p>
        </div>
        {/* Plan Badge */}
        <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold ${planColor}`}>
          <PlanIcon className="w-4 h-4" />
          Plano {planLabel}
        </span>
      </div>

      {/* Quota Bar */}
      {quota && (
        <div className="card p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Gauge className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Cota de LLM deste mês
              </span>
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {quota.used} / {quota.monthly} requisições
            </span>
          </div>
          <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                quotaPct > 80
                  ? 'bg-red-500'
                  : quotaPct > 50
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(quotaPct, 100)}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1.5">
            {quota.remaining} requisições restantes
          </p>
        </div>
      )}

      {/* Provider Selector */}
      {availableProviders.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {availableProviders.map((provider) => (
            <button
              key={provider}
              onClick={() => setSelectedProvider(provider)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                selectedProvider === provider
                  ? 'bg-primary text-white shadow-md'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              {PROVIDER_LABELS[provider] || provider}
            </button>
          ))}
        </div>
      )}

      {/* Models Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.map((model) => {
            const isActive = activeModelInfo?.active_model === model.id
            const isSelecting = selecting === model.id

            return (
              <div
                key={model.id}
                className={`card p-5 flex flex-col justify-between transition-all ${
                  isActive ? 'ring-2 ring-primary shadow-lg' : ''
                }`}
              >
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center">
                      <Cpu className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                        {model.name}
                      </h3>
                      <p className="text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {model.id}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mb-4">
                    {model.is_free ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                        <Sparkles className="w-3 h-3" /> Gratuito
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                        <Crown className="w-3 h-3" /> Premium
                      </span>
                    )}
                    {isActive && (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary">
                        <Check className="w-3 h-3" /> Ativo
                      </span>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => handleSelect(model.id)}
                  disabled={isActive || isSelecting}
                  className={`w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                    isActive
                      ? 'bg-primary text-white cursor-default'
                      : 'btn-primary'
                  } ${isSelecting ? 'opacity-70' : ''}`}
                >
                  {isActive ? (
                    <>
                      <Check className="w-4 h-4" /> Selecionado
                    </>
                  ) : isSelecting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    'Selecionar'
                  )}
                </button>
              </div>
            )
          })}
        </div>
      )}

      {!loading && models.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 mb-2">
            Nenhum modelo disponível para este provider no seu plano.
          </p>
          {planKey === 'free' && (
            <p className="text-sm text-gray-400">
              Faça upgrade para o plano Premium para acessar mais modelos.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
