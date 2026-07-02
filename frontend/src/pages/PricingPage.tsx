import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Check, Sparkles, Zap, Crown, Cpu, Gauge, Brain, X } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useAuth } from '../contexts/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

interface QuotaInfo {
  plan: string
  plan_label: string
  used: number
  monthly: number
  remaining: number
}

interface PlanFeature {
  label: string
  free: boolean | string
  premium: boolean | string
  enterprise: boolean | string
}

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    icon: Sparkles,
    color: 'green',
    price: 'R$ 0',
    period: '/mês',
    description: 'Ideal para experimentar e projetos pessoais',
    features: [
      'Modelos gratuitos (Z.AI Flash, OpenCode Free)',
      '100 requisições de LLM por mês',
      '2 provedores disponíveis',
      'Chat e NL2SQL básico',
      '1 fonte de dados conectada',
    ],
    cta: 'Plano Atual',
    highlight: false,
  },
  {
    id: 'premium',
    name: 'Premium',
    icon: Zap,
    color: 'blue',
    price: 'R$ 49',
    period: '/mês',
    description: 'Para profissionais e times pequenos',
    features: [
      'Tudo do Free +',
      'Modelos mid-cost (GPT-4o Mini, Claude Haiku, GLM-4.5)',
      '2.000 requisições de LLM por mês',
      '4 provedores disponíveis (Z.AI, OpenCode, OpenAI, Anthropic)',
      'Chat avançado + RAG híbrido',
      'Fontes de dados ilimitadas',
      'Alertas e ações automatizadas',
      'Suporte por email',
    ],
    cta: 'Fazer Upgrade',
    highlight: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    icon: Crown,
    color: 'purple',
    price: 'R$ 199',
    period: '/mês',
    description: 'Para empresas que precisam de tudo',
    features: [
      'Tudo do Premium +',
      'Todos os modelos (GPT-4o, Claude Opus, GLM-5, Grok)',
      '10.000 requisições de LLM por mês',
      'Knowledge Graph completo',
      'AI Data Analyst proativo',
      'Agent Actions (email, Jira, relatórios)',
      'API access e integrações custom',
      'Suporte prioritário 24/7',
      'SLA garantido',
    ],
    cta: 'Fazer Upgrade',
    highlight: false,
  },
]

const COMPARISON_TABLE: PlanFeature[] = [
  { label: 'Modelos gratuitos (Z.AI Flash, OpenCode Free)', free: true, premium: true, enterprise: true },
  { label: 'Modelos mid-cost (GPT-4o Mini, Claude Haiku)', free: false, premium: true, enterprise: true },
  { label: 'Modelos premium (GPT-4o, Claude Opus, GLM-5)', free: false, premium: false, enterprise: true },
  { label: 'Requisições de LLM / mês', free: '100', premium: '2.000', enterprise: '10.000' },
  { label: 'Provedores de LLM', free: '2', premium: '4', enterprise: '4' },
  { label: 'Chat e NL2SQL', free: 'Básico', premium: 'Avançado', enterprise: 'Avançado' },
  { label: 'RAG Híbrido (banco + documentos)', free: false, premium: true, enterprise: true },
  { label: 'Fontes de dados conectadas', free: '1', premium: 'Ilimitadas', enterprise: 'Ilimitadas' },
  { label: 'Alertas e Ações automatizadas', free: false, premium: true, enterprise: true },
  { label: 'Knowledge Graph', free: false, premium: false, enterprise: true },
  { label: 'AI Data Analyst proativo', free: false, premium: false, enterprise: true },
  { label: 'Agent Actions (email, Jira, relatórios)', free: false, premium: false, enterprise: true },
  { label: 'Suporte', free: 'Comunidade', premium: 'Email', enterprise: '24/7 Prioritário' },
  { label: 'SLA garantido', free: false, premium: false, enterprise: true },
]

const COLOR_MAP: Record<string, { bg: string; text: string; border: string; ring: string; btn: string }> = {
  green: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    text: 'text-green-600 dark:text-green-400',
    border: 'border-green-200 dark:border-green-800',
    ring: 'ring-green-400',
    btn: 'bg-green-600 hover:bg-green-700',
  },
  blue: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    text: 'text-blue-600 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800',
    ring: 'ring-blue-400',
    btn: 'bg-blue-600 hover:bg-blue-700',
  },
  purple: {
    bg: 'bg-purple-50 dark:bg-purple-900/20',
    text: 'text-purple-600 dark:text-purple-400',
    border: 'border-purple-200 dark:border-purple-800',
    ring: 'ring-purple-400',
    btn: 'bg-purple-600 hover:bg-purple-700',
  },
}

function getAuthHeaders() {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function FeatureValue({ value }: { value: boolean | string }) {
  if (value === true) {
    return <Check className="w-5 h-5 text-green-500 mx-auto" />
  }
  if (value === false) {
    return <X className="w-5 h-5 text-gray-300 dark:text-gray-600 mx-auto" />
  }
  return <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{value}</span>
}

export default function PricingPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [quota, setQuota] = useState<QuotaInfo | null>(null)
  const [showComparison, setShowComparison] = useState(false)
  const [requestingUpgrade, setRequestingUpgrade] = useState<string | null>(null)

  const fetchQuota = useCallback(async () => {
    try {
      const resp = await axios.get(`${API_BASE}/quota`, { headers: getAuthHeaders() })
      setQuota(resp.data)
    } catch {
      // Non-fatal
    }
  }, [])

  useEffect(() => {
    fetchQuota()
  }, [])

  const currentPlan = quota?.plan || user?.plan || 'free'
  const quotaPct = quota ? Math.round((quota.used / quota.monthly) * 100) : 0

  const handleUpgrade = async (planId: string) => {
    if (planId === currentPlan) return

    // If admin, allow direct upgrade via API
    if (user?.is_admin) {
      setRequestingUpgrade(planId)
      try {
        await axios.put(
          `${API_BASE}/auth/users/${user.username}/plan`,
          { plan: planId },
          { headers: getAuthHeaders() },
        )
        toast.success(`Plano atualizado para ${planId}!`)
        fetchQuota()
        // Update localStorage user
        const savedUser = localStorage.getItem('user')
        if (savedUser) {
          const parsed = JSON.parse(savedUser)
          parsed.plan = planId
          localStorage.setItem('user', JSON.stringify(parsed))
        }
      } catch (e: any) {
        toast.error(e?.response?.data?.detail || 'Erro ao atualizar plano.')
      } finally {
        setRequestingUpgrade(null)
      }
      return
    }

    // Non-admin: show upgrade request toast (future: integrate payment gateway)
    toast.success(
      `Solicitação de upgrade para o plano ${planId.toUpperCase()} registrada! Em breve você poderá completar o pagamento online.`,
      { duration: 5000 }
    )
    setRequestingUpgrade(planId)
    setTimeout(() => setRequestingUpgrade(null), 2000)
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/chat')}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label="Voltar"
        >
          <ArrowLeft className="w-6 h-6 text-gray-600 dark:text-gray-400" />
        </button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold gradient-text">Planos & Preços</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Escolha o plano ideal para suas necessidades de inteligência corporativa.
          </p>
        </div>
      </div>

      {/* Current Plan Status */}
      {quota && (
        <div className="card p-5 mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              {(() => {
                const PlanIcon = PLANS.find(p => p.id === currentPlan)?.icon || Sparkles
                const colors = COLOR_MAP[PLANS.find(p => p.id === currentPlan)?.color || 'green']
                return (
                  <div className={`w-12 h-12 rounded-full ${colors.bg} flex items-center justify-center`}>
                    <PlanIcon className={`w-6 h-6 ${colors.text}`} />
                  </div>
                )
              })()}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Seu plano atual: {quota.plan_label}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {quota.remaining} requisições restantes este mês
                </p>
              </div>
            </div>
            <div className="flex-1 max-w-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-gray-500 dark:text-gray-400">Uso mensal</span>
                <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                  {quota.used} / {quota.monthly}
                </span>
              </div>
              <div className="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    quotaPct > 80 ? 'bg-red-500' : quotaPct > 50 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(quotaPct, 100)}%` }}
                />
              </div>
            </div>
          </div>
          {currentPlan !== 'enterprise' && quotaPct > 70 && (
            <div className="mt-4 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
              <p className="text-sm text-yellow-700 dark:text-yellow-400">
                ⚠️ Você está usando {quotaPct}% da sua quota mensal. Considere fazer upgrade para evitar interrupções.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Plan Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        {PLANS.map((plan) => {
          const colors = COLOR_MAP[plan.color]
          const isCurrent = plan.id === currentPlan
          const isUpgrade = PLANS.findIndex(p => p.id === plan.id) > PLANS.findIndex(p => p.id === currentPlan)
          const PlanIcon = plan.icon

          return (
            <div
              key={plan.id}
              className={`card p-6 flex flex-col relative transition-all ${
                plan.highlight
                  ? `ring-2 ${colors.ring} shadow-xl scale-105`
                  : ''
              } ${isCurrent ? `border-2 ${colors.border}` : ''}`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${colors.btn}`}>
                    Mais Popular
                  </span>
                </div>
              )}

              <div className="flex items-center gap-3 mb-4">
                <div className={`w-12 h-12 rounded-full ${colors.bg} flex items-center justify-center`}>
                  <PlanIcon className={`w-6 h-6 ${colors.text}`} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{plan.name}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{plan.description}</p>
                </div>
              </div>

              <div className="mb-5">
                <span className="text-4xl font-bold text-gray-900 dark:text-gray-100">{plan.price}</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">{plan.period}</span>
              </div>

              <ul className="space-y-2.5 mb-6 flex-1">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <Check className={`w-4 h-4 ${colors.text} mt-0.5 flex-shrink-0`} />
                    <span className="text-sm text-gray-600 dark:text-gray-400">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleUpgrade(plan.id)}
                disabled={isCurrent || requestingUpgrade === plan.id}
                className={`w-full py-3 rounded-xl font-semibold transition-all ${
                  isCurrent
                    ? 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 cursor-default'
                    : plan.highlight
                    ? `${colors.btn} text-white shadow-lg`
                    : `border-2 ${colors.border} ${colors.text} hover:${colors.bg}`
                } ${requestingUpgrade === plan.id ? 'opacity-70' : ''}`}
              >
                {isCurrent
                  ? 'Plano Atual'
                  : requestingUpgrade === plan.id
                  ? 'Processando...'
                  : isUpgrade
                  ? plan.cta
                  : 'Downgrade'}
              </button>
            </div>
          )
        })}
      </div>

      {/* Comparison Table Toggle */}
      <div className="text-center mb-6">
        <button
          onClick={() => setShowComparison(!showComparison)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-primary hover:bg-primary/10 transition-colors"
        >
          {showComparison ? 'Ocultar' : 'Ver'} comparação detalhada
        </button>
      </div>

      {showComparison && (
        <div className="card overflow-hidden mb-10">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">Recurso</th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">
                    <span className="inline-flex items-center gap-1">
                      <Sparkles className="w-4 h-4 text-green-500" /> Free
                    </span>
                  </th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">
                    <span className="inline-flex items-center gap-1">
                      <Zap className="w-4 h-4 text-blue-500" /> Premium
                    </span>
                  </th>
                  <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600 dark:text-gray-400">
                    <span className="inline-flex items-center gap-1">
                      <Crown className="w-4 h-4 text-purple-500" /> Enterprise
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {COMPARISON_TABLE.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  >
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{row.label}</td>
                    <td className="px-4 py-3 text-center"><FeatureValue value={row.free} /></td>
                    <td className="px-4 py-3 text-center"><FeatureValue value={row.premium} /></td>
                    <td className="px-4 py-3 text-center"><FeatureValue value={row.enterprise} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Feature Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="card p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center mx-auto mb-3">
            <Cpu className="w-6 h-6 text-blue-500" />
          </div>
          <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Múltiplos LLMs</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Acesso a GPT-4o, Claude, GLM e mais — escolha o melhor modelo para cada tarefa.
          </p>
        </div>
        <div className="card p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-green-50 dark:bg-green-900/20 flex items-center justify-center mx-auto mb-3">
            <Gauge className="w-6 h-6 text-green-500" />
          </div>
          <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Quota Flexível</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            De 100 a 10.000 requisições mensais. Reset automático a cada mês.
          </p>
        </div>
        <div className="card p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center mx-auto mb-3">
            <Brain className="w-6 h-6 text-purple-500" />
          </div>
          <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">IA Avançada</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            RAG híbrido, AI Data Analyst proativo e Agent Actions no plano Enterprise.
          </p>
        </div>
      </div>

      {/* FAQ */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Perguntas Frequentes
        </h3>
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-1">
              Posso cancelar a qualquer momento?
            </h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Sim. Ao cancelar, você volta para o plano Free no final do período pago. Sem multa.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-1">
              A quota acumula de um mês para o outro?
            </h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Não. A quota é resetada automaticamente no início de cada mês. O contador volta a zero.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-1">
              Posso fazer upgrade a qualquer momento?
            </h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Sim. O upgrade é imediato. A nova quota já fica disponível para uso.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-1">
              Quais modelos de LLM estão disponíveis?
            </h4>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Free: GLM-4.5-Flash e modelos gratuitos do OpenCode Zen. Premium: GPT-4o Mini, Claude Haiku, GLM-4.5.
              Enterprise: GPT-4o, Claude Opus, GLM-5, Grok e todos os anteriores.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
