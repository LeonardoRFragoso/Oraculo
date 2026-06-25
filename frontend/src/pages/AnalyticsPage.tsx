import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import {
  Brain, RefreshCw, AlertTriangle,
  TrendingUp, Zap, ChevronDown, ChevronRight, Database, MessageSquare
} from 'lucide-react'
import toast from 'react-hot-toast'
import { listDataSources, analyzeDataSource, AnalysisReport, DataSource } from '../services/api'

const STATUS_CONFIG: Record<string, { color: string; bg: string; icon: string }> = {
  good:     { color: 'text-green-600',  bg: 'bg-green-50 dark:bg-green-900/20',  icon: '✅' },
  warning:  { color: 'text-yellow-600', bg: 'bg-yellow-50 dark:bg-yellow-900/20', icon: '⚠️' },
  critical: { color: 'text-red-600',    bg: 'bg-red-50 dark:bg-red-900/20',       icon: '🚨' },
  info:     { color: 'text-blue-600',   bg: 'bg-blue-50 dark:bg-blue-900/20',     icon: 'ℹ️' },
}
const SEV_COLOR: Record<string, string> = {
  critical: '#ef4444', warning: '#f59e0b', info: '#3b82f6',
}

export default function AnalyticsPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [sources, setSources] = useState<DataSource[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [report, setReport] = useState<AnalysisReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [expandedDs, setExpandedDs] = useState<string | null>(null)

  useEffect(() => {
    listDataSources().then(s => {
      const connected = s.filter(x => x.status === 'connected')
      setSources(connected)
      const paramId = searchParams.get('source')
      if (paramId && connected.some(x => x.id === paramId)) {
        setSelected(paramId)
      } else if (connected.length > 0) {
        setSelected(connected[0].id)
      }
    })
  }, [searchParams])

  useEffect(() => {
    if (!selected) return
    setReport(null)
    setLoading(true)
    analyzeDataSource(selected)
      .then(setReport)
      .catch(() => toast.error('Erro na análise'))
      .finally(() => setLoading(false))
  }, [selected])

  const selectedSource = sources.find(s => s.id === selected)

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold gradient-text flex items-center gap-3">
              <Brain className="w-8 h-8 text-primary" />
              AI Data Analyst
            </h1>
            <p className="text-sm text-gray-500 mt-1">Insights proativos gerados automaticamente</p>
          </div>
          <div className="flex items-center gap-2">
            {selected && (
              <button
                onClick={() => navigate(`/chat?source=${selected}`)}
                className="btn-primary flex items-center gap-2 text-sm"
              >
                <MessageSquare className="w-4 h-4" />
                Perguntar sobre a fonte
              </button>
            )}
            {sources.length > 1 && (
              <select
                className="input text-sm"
                value={selected || ''}
                onChange={e => setSelected(e.target.value)}
              >
                {sources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            )}
          </div>
        </div>

        {sources.length === 0 ? (
          <NoSourcesCard />
        ) : loading ? (
          <LoadingCard name={selectedSource?.name} />
        ) : report ? (
          <ReportView report={report} expandedDs={expandedDs} setExpandedDs={setExpandedDs} />
        ) : null}
      </div>
    </div>
  )
}

function ReportView({ report, expandedDs, setExpandedDs }: {
  report: AnalysisReport
  expandedDs: string | null
  setExpandedDs: (s: string | null) => void
}) {
  const allKpis = report.datasets.flatMap(d => d.kpis)
  const topKpis = allKpis.filter(k => ['R$', '%'].includes(k.unit)).slice(0, 4)

  const anomalyChartData = report.datasets.flatMap(d =>
    d.anomalies.map(a => ({ name: a.column.slice(0, 15), severity: a.severity }))
  ).slice(0, 8)

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard label="KPIs Gerados" value={report.total_kpis} icon={<TrendingUp className="w-5 h-5" />} color="text-blue-500" />
        <SummaryCard label="Anomalias" value={report.total_anomalies} icon={<AlertTriangle className="w-5 h-5" />} color="text-yellow-500" />
        <SummaryCard label="Críticos" value={report.critical_count} icon={<Zap className="w-5 h-5" />} color={report.critical_count > 0 ? 'text-red-500' : 'text-green-500'} />
        <SummaryCard label="Datasets" value={report.datasets.length} icon={<Database className="w-5 h-5" />} color="text-purple-500" />
      </div>

      {/* Executive summary */}
      <div className="card">
        <h2 className="font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
          <Brain className="w-4 h-4 text-primary" /> Resumo Executivo
        </h2>
        <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
          {report.executive_summary}
        </pre>
      </div>

      {/* Top KPIs bar chart */}
      {topKpis.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">📊 KPIs Principais</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {topKpis.map((k, i) => {
              const cfg = STATUS_CONFIG[k.status] || STATUS_CONFIG.info
              const val = typeof k.value === 'number'
                ? k.unit === 'R$' ? `R$ ${k.value.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}`
                : `${k.value.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}${k.unit}`
                : `${k.value} ${k.unit}`
              return (
                <div key={i} className={`p-4 rounded-xl ${cfg.bg}`}>
                  <p className="text-xs text-gray-500 mb-1">{k.name}</p>
                  <p className={`text-xl font-bold ${cfg.color}`}>{val}</p>
                  {k.description && <p className="text-xs text-gray-400 mt-1 truncate">{k.description}</p>}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Anomalies */}
      {report.total_anomalies > 0 && (
        <div className="card">
          <h2 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">⚠️ Anomalias Detectadas</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-2">
              {report.datasets.flatMap(d => d.anomalies).slice(0, 8).map((a, i) => (
                <div key={i} className={`flex items-start gap-3 p-3 rounded-lg ${STATUS_CONFIG[a.severity]?.bg || ''}`}>
                  <span className="text-lg">{a.emoji}</span>
                  <div>
                    <p className={`text-sm font-medium ${STATUS_CONFIG[a.severity]?.color || ''}`}>
                      [{a.severity.toUpperCase()}] {a.column}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">{a.message}</p>
                  </div>
                </div>
              ))}
            </div>
            {anomalyChartData.length > 0 && (
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={anomalyChartData} layout="vertical">
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={() => ''} />
                    <Bar dataKey="severity" radius={4}>
                      {anomalyChartData.map((entry, i) => (
                        <Cell key={i} fill={SEV_COLOR[entry.severity] || '#94a3b8'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Dataset details */}
      <div className="space-y-3">
        {report.datasets.map(ds => (
          <div key={ds.dataset_name} className="card">
            <button
              className="w-full flex items-center justify-between"
              onClick={() => setExpandedDs(expandedDs === ds.dataset_name ? null : ds.dataset_name)}
            >
              <div className="flex items-center gap-3">
                <Database className="w-5 h-5 text-primary" />
                <div className="text-left">
                  <p className="font-semibold text-gray-900 dark:text-gray-100">{ds.dataset_name}</p>
                  <p className="text-xs text-gray-500">
                    {ds.row_count.toLocaleString()} linhas · {ds.domain.toUpperCase()} · {ds.kpis.length} KPIs · {ds.anomalies.length} anomalias
                  </p>
                </div>
              </div>
              {expandedDs === ds.dataset_name
                ? <ChevronDown className="w-4 h-4 text-gray-400" />
                : <ChevronRight className="w-4 h-4 text-gray-400" />}
            </button>

            {expandedDs === ds.dataset_name && (
              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs text-gray-500 border-b border-gray-100 dark:border-gray-700">
                        <th className="pb-2 font-medium">KPI</th>
                        <th className="pb-2 font-medium">Valor</th>
                        <th className="pb-2 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ds.kpis.map((k, i) => {
                        const cfg = STATUS_CONFIG[k.status] || STATUS_CONFIG.info
                        return (
                          <tr key={i} className="border-b border-gray-50 dark:border-gray-800">
                            <td className="py-1.5 text-gray-700 dark:text-gray-300">{k.name}</td>
                            <td className="py-1.5 font-medium text-gray-900 dark:text-gray-100">
                              {typeof k.value === 'number' ? k.value.toLocaleString('pt-BR', { maximumFractionDigits: 2 }) : k.value}
                              {' '}{k.unit}
                            </td>
                            <td className="py-1.5">
                              <span className={`text-xs font-medium ${cfg.color}`}>{cfg.icon} {k.status}</span>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function SummaryCard({ label, value, icon, color }: { label: string; value: number; icon: React.ReactNode; color: string }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`${color}`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  )
}

function LoadingCard({ name }: { name?: string }) {
  return (
    <div className="card flex flex-col items-center py-16 gap-4">
      <RefreshCw className="w-10 h-10 text-primary animate-spin" />
      <div className="text-center">
        <p className="font-semibold text-gray-700 dark:text-gray-300">Analisando {name}...</p>
        <p className="text-sm text-gray-500 mt-1">Gerando KPIs e detectando anomalias</p>
      </div>
    </div>
  )
}

function NoSourcesCard() {
  return (
    <div className="card text-center py-16">
      <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
      <p className="font-semibold text-gray-600 dark:text-gray-400">Nenhuma fonte conectada</p>
      <p className="text-sm text-gray-500 mt-2">
        Vá para <strong>Fontes de Dados</strong> e conecte uma fonte para ver insights.
      </p>
    </div>
  )
}
