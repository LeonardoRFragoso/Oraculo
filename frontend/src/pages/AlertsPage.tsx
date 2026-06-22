import { useState, useEffect } from 'react'
import { Bell, Zap, RefreshCw, Send, FileText, PlusCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import toast from 'react-hot-toast'
import { listAlerts, listDataSources, actOnSource, DataSource } from '../services/api'

const SEV_CONFIG: Record<string, { bg: string; border: string; label: string; icon: string }> = {
  critical: { bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-l-4 border-red-500', label: 'CRÍTICO', icon: '🚨' },
  warning:  { bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-l-4 border-yellow-500', label: 'AVISO', icon: '⚠️' },
  info:     { bg: 'bg-blue-50 dark:bg-blue-900/20', border: 'border-l-4 border-blue-500', label: 'INFO', icon: 'ℹ️' },
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([])
  const [sources, setSources] = useState<DataSource[]>([])
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(false)
  const [selectedSource, setSelectedSource] = useState<string>('')
  const [instruction, setInstruction] = useState('')
  const [dryRun, setDryRun] = useState(false)
  const [lastResult, setLastResult] = useState<any>(null)

  const loadAll = async () => {
    setLoading(true)
    try {
      const [alertsData, sourcesData] = await Promise.all([listAlerts(50), listDataSources()])
      setAlerts(alertsData.alerts)
      const connected = sourcesData.filter(s => s.status === 'connected')
      setSources(connected)
      if (connected.length > 0 && !selectedSource) setSelectedSource(connected[0].id)
    } catch { toast.error('Erro ao carregar dados') }
    finally { setLoading(false) }
  }

  useEffect(() => { loadAll() }, [])

  const handleAct = async () => {
    if (!selectedSource) { toast.error('Selecione uma fonte'); return }
    setActing(true)
    setLastResult(null)
    try {
      const result = await actOnSource(selectedSource, instruction || undefined, {}, dryRun)
      setLastResult(result)
      if (!dryRun) {
        toast.success(`${result.actions_executed} ação(ões) executada(s)!`)
        loadAll()
      } else {
        toast.success('Plano de execução calculado (dry run)')
      }
    } catch { toast.error('Erro ao executar ação') }
    finally { setActing(false) }
  }

  const criticalCount = alerts.filter(a => a.severity === 'critical').length

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold gradient-text flex items-center gap-3">
              <Bell className="w-8 h-8 text-primary" />
              Alertas & Agent Actions
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {alerts.length} alertas · {criticalCount > 0 ? `🚨 ${criticalCount} críticos` : '✅ Sem críticos'}
            </p>
          </div>
          <button onClick={loadAll} disabled={loading} className="btn-secondary p-2">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Action Panel */}
          <div className="card">
            <h2 className="font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-primary" /> Executar Ação
            </h2>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-600 dark:text-gray-400">Fonte de dados</label>
                <select
                  className="input mt-1 w-full text-sm"
                  value={selectedSource}
                  onChange={e => setSelectedSource(e.target.value)}
                >
                  {sources.length === 0
                    ? <option value="">Nenhuma fonte conectada</option>
                    : sources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Instrução (deixe vazio para auto-trigger por anomalia)
                </label>
                <textarea
                  className="input mt-1 w-full text-sm resize-none"
                  rows={3}
                  placeholder="Ex: Gerar relatório markdown&#10;Ex: Enviar email para cfo@empresa.com&#10;Ex: Criar alerta"
                  value={instruction}
                  onChange={e => setInstruction(e.target.value)}
                />
              </div>

              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
                  <input
                    type="checkbox"
                    className="rounded"
                    checked={dryRun}
                    onChange={e => setDryRun(e.target.checked)}
                  />
                  Simular (dry run)
                </label>
              </div>

              <button
                onClick={handleAct}
                disabled={acting || sources.length === 0}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {acting
                  ? <RefreshCw className="w-4 h-4 animate-spin" />
                  : <Zap className="w-4 h-4" />}
                {acting ? 'Executando...' : dryRun ? 'Simular' : 'Executar'}
              </button>
            </div>

            {/* Last result */}
            {lastResult && (
              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
                  Plano executado · {lastResult.kpi_count} KPIs · {lastResult.anomaly_count} anomalias
                </p>
                <div className="space-y-2">
                  {lastResult.results?.map((r: any, i: number) => (
                    <ActionResultBadge key={i} result={r} />
                  ))}
                </div>
                {lastResult.results?.length === 0 && (
                  <p className="text-sm text-gray-500">Nenhuma ação necessária.</p>
                )}
              </div>
            )}
          </div>

          {/* Quick action buttons */}
          <div className="space-y-3">
            <h2 className="font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-500" /> Ações Rápidas
            </h2>
            {[
              { icon: <FileText className="w-4 h-4" />, label: 'Gerar Relatório Markdown', instr: 'Gerar relatorio markdown' },
              { icon: <FileText className="w-4 h-4" />, label: 'Gerar Relatório JSON', instr: 'Gerar relatorio', params: { format: 'json' } },
              { icon: <PlusCircle className="w-4 h-4" />, label: 'Criar Alerta (auto)', instr: '' },
              { icon: <Send className="w-4 h-4" />, label: 'Simular envio de email', instr: 'Enviar email para admin@empresa.com', dryRun: true },
            ].map((qa, i) => (
              <button
                key={i}
                className="w-full card hover:shadow-md transition-shadow flex items-center gap-3 text-sm text-left p-4"
                onClick={async () => {
                  if (!selectedSource) { toast.error('Selecione uma fonte primeiro'); return }
                  setActing(true)
                  setLastResult(null)
                  try {
                    const result = await actOnSource(selectedSource, qa.instr || undefined, (qa as any).params, qa.dryRun || false)
                    setLastResult(result)
                    toast.success(`${result.actions_executed} ação(ões) executada(s)`)
                    if (!qa.dryRun) loadAll()
                  } catch { toast.error('Erro') }
                  finally { setActing(false) }
                }}
                disabled={acting}
              >
                <span className="text-primary">{qa.icon}</span>
                <span className="text-gray-700 dark:text-gray-300">{qa.label}</span>
                {qa.dryRun && <span className="ml-auto text-xs text-gray-400 italic">simulação</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Alert history */}
        <div className="mt-6">
          <h2 className="font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <Bell className="w-5 h-5" /> Histórico de Alertas
          </h2>
          {loading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="w-6 h-6 text-primary animate-spin" />
            </div>
          ) : alerts.length === 0 ? (
            <div className="card text-center py-10 text-gray-400">
              <Bell className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p>Nenhum alerta registrado ainda.</p>
              <p className="text-sm mt-1">Execute uma ação para criar alertas.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {alerts.map((alert, i) => {
                const cfg = SEV_CONFIG[alert.severity] || SEV_CONFIG.info
                const ago = formatDistanceToNow(new Date(alert.created_at), { addSuffix: true, locale: ptBR })
                return (
                  <div key={i} className={`p-4 rounded-xl ${cfg.bg} ${cfg.border}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-2 flex-1 min-w-0">
                        <span className="text-lg mt-0.5">{cfg.icon}</span>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-900 dark:text-gray-100 text-sm truncate">{alert.title}</p>
                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5 line-clamp-2">{alert.message}</p>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <span className="text-xs font-medium text-gray-500">{ago}</span>
                        <p className="text-xs text-gray-400">{alert.source_name}</p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ActionResultBadge({ result }: { result: any }) {
  const statusColor = result.status === 'success' ? 'text-green-600 bg-green-50 dark:bg-green-900/20'
    : result.status === 'dry_run' ? 'text-blue-600 bg-blue-50 dark:bg-blue-900/20'
    : 'text-red-600 bg-red-50 dark:bg-red-900/20'

  return (
    <div className={`p-3 rounded-lg ${statusColor}`}>
      <div className="flex items-center gap-2 text-sm font-medium">
        <Zap className="w-3.5 h-3.5" />
        <span>{result.action}</span>
        <span className="ml-auto text-xs opacity-70 uppercase">{result.status}</span>
      </div>
      <p className="text-xs mt-1 opacity-80">{result.message}</p>
      {result.artifact && (
        <p className="text-xs mt-1 font-mono opacity-60 truncate">📁 {result.artifact}</p>
      )}
    </div>
  )
}
