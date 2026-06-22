import { useState, useEffect, useRef } from 'react'
import {
  Database, Upload, Plus, Zap, Trash2, RefreshCw,
  CheckCircle, XCircle, Clock, ChevronDown, ChevronRight,
  Table, BarChart2
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  listDataSources, connectDataSource, deleteDataSource,
  uploadDataSource, registerDataSource, DataSource
} from '../services/api'

const TYPE_ICONS: Record<string, string> = {
  csv: '📄', excel: '📊', sqlite: '🗃️', postgresql: '🐘',
  mysql: '🐬', json: '{}', parquet: '🔷', pdf: '📕',
  docx: '📝', txt: '📃', xml: '🏷️',
}
const STATUS_COLOR: Record<string, string> = {
  connected: 'text-green-500', error: 'text-red-500',
  registered: 'text-yellow-500', connecting: 'text-blue-400',
}

export default function DataSourcesPage() {
  const [sources, setSources] = useState<DataSource[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const load = async () => {
    try {
      const data = await listDataSources()
      setSources(data)
    } catch { toast.error('Erro ao carregar fontes') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleConnect = async (id: string) => {
    setConnecting(id)
    try {
      await connectDataSource(id)
      toast.success('Fonte conectada e analisada!')
      load()
    } catch { toast.error('Erro ao conectar fonte') }
    finally { setConnecting(null) }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Remover "${name}"?`)) return
    try {
      await deleteDataSource(id)
      toast.success('Fonte removida')
      setSources(s => s.filter(x => x.id !== id))
    } catch { toast.error('Erro ao remover') }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const id = toast.loading(`Enviando ${file.name}...`)
    try {
      const src = await uploadDataSource(file)
      toast.dismiss(id)
      toast.success(`"${src.name}" registrado! Clique em Conectar para analisar.`)
      load()
    } catch {
      toast.dismiss(id)
      toast.error('Erro no upload')
    }
    e.target.value = ''
  }

  const connected = sources.filter(s => s.status === 'connected')
  const others = sources.filter(s => s.status !== 'connected')

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold gradient-text">Fontes de Dados</h1>
            <p className="text-sm text-gray-500 mt-1">
              {sources.length} fontes · {connected.length} conectadas
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => fileRef.current?.click()}
              className="btn-secondary flex items-center gap-2 text-sm"
            >
              <Upload className="w-4 h-4" /> Upload
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" /> Adicionar
            </button>
            <input ref={fileRef} type="file"
              accept=".csv,.xlsx,.xls,.json,.parquet,.pdf,.docx,.txt,.sqlite,.db"
              className="hidden" onChange={handleUpload} />
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <RefreshCw className="w-8 h-8 text-primary animate-spin" />
          </div>
        ) : sources.length === 0 ? (
          <EmptyState onUpload={() => fileRef.current?.click()} onAdd={() => setShowAddModal(true)} />
        ) : (
          <div className="space-y-3">
            {[...connected, ...others].map(src => (
              <SourceCard
                key={src.id}
                source={src}
                isConnecting={connecting === src.id}
                expanded={expanded === src.id}
                onToggle={() => setExpanded(expanded === src.id ? null : src.id)}
                onConnect={() => handleConnect(src.id)}
                onDelete={() => handleDelete(src.id, src.name)}
              />
            ))}
          </div>
        )}
      </div>

      {showAddModal && (
        <AddSourceModal onClose={() => setShowAddModal(false)} onAdded={load} />
      )}
    </div>
  )
}

function SourceCard({ source, isConnecting, expanded, onToggle, onConnect, onDelete }: {
  source: DataSource; isConnecting: boolean; expanded: boolean
  onToggle: () => void; onConnect: () => void; onDelete: () => void
}) {
  const icon = TYPE_ICONS[source.connector_type] || '🔌'
  const statusColor = STATUS_COLOR[source.status] || 'text-gray-400'
  const domain = source.domain_summary?.primary_domain

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="flex items-center gap-4">
        <span className="text-2xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{source.name}</h3>
            {domain && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium capitalize">
                {domain}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
            <span className="uppercase font-mono">{source.connector_type}</span>
            <span className={`font-medium ${statusColor} flex items-center gap-1`}>
              {source.status === 'connected' && <CheckCircle className="w-3 h-3" />}
              {source.status === 'error' && <XCircle className="w-3 h-3" />}
              {source.status === 'registered' && <Clock className="w-3 h-3" />}
              {source.status}
            </span>
            {source.datasets?.length > 0 && (
              <span><Table className="inline w-3 h-3 mr-0.5" />{source.datasets.length} tabelas</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {source.status !== 'connected' && (
            <button
              onClick={onConnect}
              disabled={isConnecting}
              className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1.5"
            >
              {isConnecting
                ? <RefreshCw className="w-3 h-3 animate-spin" />
                : <Zap className="w-3 h-3" />}
              {isConnecting ? 'Conectando...' : 'Conectar'}
            </button>
          )}
          {source.status === 'connected' && (
            <button
              onClick={onConnect}
              disabled={isConnecting}
              className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5"
            >
              {isConnecting
                ? <RefreshCw className="w-3 h-3 animate-spin" />
                : <RefreshCw className="w-3 h-3" />}
              Re-analisar
            </button>
          )}
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-bg text-gray-400"
          >
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
          <button
            onClick={onDelete}
            className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-400"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {expanded && source.datasets?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Datasets Descobertos</p>
          <div className="space-y-2">
            {source.datasets.map((ds: any, i: number) => (
              <div key={i} className="flex items-center gap-3 text-sm p-2 rounded-lg bg-gray-50 dark:bg-dark-bg">
                <BarChart2 className="w-4 h-4 text-primary flex-shrink-0" />
                <span className="font-medium flex-1">{ds.name}</span>
                <span className="text-gray-500 text-xs">{ds.row_count?.toLocaleString()} linhas</span>
                <span className="text-gray-500 text-xs">{ds.column_count} colunas</span>
                {ds.domain && (
                  <span className="text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary capitalize">{ds.domain}</span>
                )}
              </div>
            ))}
          </div>
          {source.domain_summary?.quality && (
            <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
              <span>Qualidade dos dados:</span>
              <QualityBar summary={source.domain_summary.quality} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function QualityBar({ summary }: { summary: any }) {
  const score = summary?.overall_score ?? summary?.avg_score ?? null
  if (score === null) return null
  const color = score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${score}%` }} />
      </div>
      <span className="font-medium">{score.toFixed(0)}/100</span>
    </div>
  )
}

function EmptyState({ onUpload, onAdd }: { onUpload: () => void; onAdd: () => void }) {
  return (
    <div className="text-center py-20">
      <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-400 mb-2">
        Nenhuma fonte conectada
      </h3>
      <p className="text-gray-500 text-sm mb-6">
        Conecte um banco de dados ou faça upload de um arquivo para começar.
      </p>
      <div className="flex justify-center gap-3">
        <button onClick={onUpload} className="btn-secondary flex items-center gap-2">
          <Upload className="w-4 h-4" /> Upload de Arquivo
        </button>
        <button onClick={onAdd} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Conectar Banco
        </button>
      </div>
    </div>
  )
}

function AddSourceModal({ onClose, onAdded }: { onClose: () => void; onAdded: () => void }) {
  const [form, setForm] = useState({
    name: '', connector_type: 'sqlite', path: '',
    host: 'localhost', port: '5432', database: '', user: '', password: '',
  })
  const [saving, setSaving] = useState(false)

  const fileTypes = ['csv', 'excel', 'json', 'parquet', 'pdf', 'docx', 'txt', 'xml']
  const dbTypes = ['sqlite', 'postgresql', 'mysql']
  const isFile = fileTypes.includes(form.connector_type)

  const buildConfig = () => {
    if (isFile) return { path: form.path }
    return {
      host: form.host, port: Number(form.port),
      database: form.database, user: form.user, password: form.password,
    }
  }

  const handleSave = async () => {
    if (!form.name) { toast.error('Nome obrigatório'); return }
    setSaving(true)
    try {
      await registerDataSource({
        name: form.name, connector_type: form.connector_type,
        config: buildConfig(),
      })
      toast.success('Fonte registrada! Clique em Conectar para analisar.')
      onAdded(); onClose()
    } catch { toast.error('Erro ao registrar fonte') }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-dark-surface rounded-2xl shadow-2xl w-full max-w-lg p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Adicionar Fonte</h2>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Nome</label>
            <input
              className="input mt-1 w-full"
              placeholder="Ex: Vendas 2025"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Tipo</label>
            <select
              className="input mt-1 w-full"
              value={form.connector_type}
              onChange={e => setForm(f => ({ ...f, connector_type: e.target.value }))}
            >
              <optgroup label="Arquivos">{fileTypes.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}</optgroup>
              <optgroup label="Bancos">{dbTypes.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}</optgroup>
            </select>
          </div>
          {isFile ? (
            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Caminho do arquivo</label>
              <input
                className="input mt-1 w-full font-mono text-sm"
                placeholder="/caminho/para/arquivo.csv"
                value={form.path}
                onChange={e => setForm(f => ({ ...f, path: e.target.value }))}
              />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {[
                { key: 'host', label: 'Host' }, { key: 'port', label: 'Porta' },
                { key: 'database', label: 'Banco' }, { key: 'user', label: 'Usuário' },
              ].map(({ key, label }) => (
                <div key={key}>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>
                  <input
                    className="input mt-1 w-full"
                    value={(form as any)[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  />
                </div>
              ))}
              <div className="col-span-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Senha</label>
                <input type="password" className="input mt-1 w-full" value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
              </div>
            </div>
          )}
        </div>
        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="btn-secondary">Cancelar</button>
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
            {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            Registrar
          </button>
        </div>
      </div>
    </div>
  )
}
