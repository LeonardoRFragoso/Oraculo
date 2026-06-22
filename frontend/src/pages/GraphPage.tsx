import { useState, useEffect, useRef } from 'react'
import { Share2, Search, RefreshCw, ZoomIn, ZoomOut, Info } from 'lucide-react'
import toast from 'react-hot-toast'
import {
  listDataSources, buildGraph, getGraph, searchGraph,
  getGraphEntity, DataSource, GraphResponse
} from '../services/api'

const TYPE_COLORS: Record<string, string> = {
  CUSTOMER: '#4F81BD', PRODUCT: '#C0504D', EMPLOYEE: '#9BBB59',
  LOCATION: '#F79646', CATEGORY: '#8064A2', STATUS: '#4BACC6',
  DEPARTMENT: '#F2AB27', BRAND: '#D24726',
}

export default function GraphPage() {
  const [sources, setSources] = useState<DataSource[]>([])
  const [selected, setSelected] = useState<string>('')
  const [graphData, setGraphData] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [building, setBuilding] = useState(false)
  const [searchQ, setSearchQ] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [focusEntity, setFocusEntity] = useState<any>(null)
  const [activeNode, setActiveNode] = useState<string | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const nodesPos = useRef<Map<string, { x: number; y: number }>>(new Map())
  const scale = useRef(1)
  const offset = useRef({ x: 0, y: 0 })
  const dragging = useRef<{ node: string | null; ox: number; oy: number }>({ node: null, ox: 0, oy: 0 })

  useEffect(() => {
    listDataSources().then(s => {
      const connected = s.filter(x => x.status === 'connected')
      setSources(connected)
      if (connected.length > 0) setSelected(connected[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    setGraphData(null)
    setFocusEntity(null)
    setActiveNode(null)
    getGraph(selected)
      .then(d => { setGraphData(d); layoutGraph(d) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [selected])

  useEffect(() => {
    if (graphData) drawCanvas()
  }, [graphData, activeNode])

  const layoutGraph = (data: GraphResponse) => {
    const nodes = data.graph.nodes
    const n = nodes.length
    const W = canvasRef.current?.width || 800
    const H = canvasRef.current?.height || 500
    const cx = W / 2, cy = H / 2, r = Math.min(cx, cy) * 0.75
    nodesPos.current.clear()
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / n
      nodesPos.current.set(node.id, {
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      })
    })
  }

  const drawCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas || !graphData) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.save()
    ctx.translate(offset.current.x, offset.current.y)
    ctx.scale(scale.current, scale.current)

    // Draw edges
    graphData.graph.edges.forEach(edge => {
      const from = nodesPos.current.get(edge.from)
      const to = nodesPos.current.get(edge.to)
      if (!from || !to) return
      ctx.beginPath()
      ctx.moveTo(from.x, from.y)
      ctx.lineTo(to.x, to.y)
      ctx.strokeStyle = `rgba(150,150,170,${Math.max(0.15, edge.weight)})`
      ctx.lineWidth = Math.max(1, edge.weight * 3)
      ctx.stroke()
      // Arrow head
      const angle = Math.atan2(to.y - from.y, to.x - from.x)
      const dist = Math.hypot(to.x - from.x, to.y - from.y)
      const ar = Math.min(20, dist * 0.3)
      ctx.beginPath()
      ctx.moveTo(
        to.x - ar * Math.cos(angle - 0.4),
        to.y - ar * Math.sin(angle - 0.4)
      )
      ctx.lineTo(to.x, to.y)
      ctx.lineTo(
        to.x - ar * Math.cos(angle + 0.4),
        to.y - ar * Math.sin(angle + 0.4)
      )
      ctx.fillStyle = 'rgba(150,150,170,0.5)'
      ctx.fill()
    })

    // Draw nodes
    graphData.graph.nodes.forEach(node => {
      const pos = nodesPos.current.get(node.id)
      if (!pos) return
      const r = node.size || 12
      const color = TYPE_COLORS[node.type] || '#888'
      const isActive = node.id === activeNode
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, r, 0, 2 * Math.PI)
      ctx.fillStyle = isActive ? '#fff' : color
      ctx.fill()
      ctx.strokeStyle = isActive ? color : 'rgba(255,255,255,0.7)'
      ctx.lineWidth = isActive ? 3 : 1.5
      ctx.stroke()
      ctx.fillStyle = '#111'
      ctx.font = `${isActive ? 'bold ' : ''}${Math.min(12, r)}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(node.label.slice(0, 12), pos.x, pos.y + r + 8)
    })
    ctx.restore()
  }

  const handleBuild = async () => {
    if (!selected) return
    setBuilding(true)
    try {
      const data = await buildGraph(selected)
      setGraphData(data)
      layoutGraph(data)
      toast.success(`Grafo construído: ${data.stats.node_count} nós, ${data.stats.edge_count} arestas`)
    } catch { toast.error('Erro ao construir grafo') }
    finally { setBuilding(false) }
  }

  const handleSearch = async () => {
    if (!selected || !searchQ.trim()) return
    try {
      const results = await searchGraph(selected, searchQ)
      setSearchResults(results)
    } catch { toast.error('Erro na busca') }
  }

  const handleNodeClick = async (entityId: string) => {
    setActiveNode(entityId)
    try {
      const detail = await getGraphEntity(selected, entityId, 1)
      setFocusEntity(detail)
    } catch {}
  }

  // Canvas mouse events
  const getNodeAt = (cx: number, cy: number): string | null => {
    const canvas = canvasRef.current
    if (!canvas) return null
    const rect = canvas.getBoundingClientRect()
    const mx = (cx - rect.left - offset.current.x) / scale.current
    const my = (cy - rect.top - offset.current.y) / scale.current
    for (const [id, pos] of nodesPos.current) {
      const r = 16
      if (Math.hypot(mx - pos.x, my - pos.y) < r) return id
    }
    return null
  }

  const onMouseDown = (e: React.MouseEvent) => {
    const node = getNodeAt(e.clientX, e.clientY)
    if (node) {
      dragging.current = { node, ox: e.clientX, oy: e.clientY }
      handleNodeClick(node)
    } else {
      dragging.current = { node: null, ox: e.clientX, oy: e.clientY }
    }
  }
  const onMouseMove = (e: React.MouseEvent) => {
    const d = dragging.current
    if (!d.ox && !d.oy) return
    const dx = e.clientX - d.ox
    const dy = e.clientY - d.oy
    if (d.node) {
      const pos = nodesPos.current.get(d.node)
      if (pos) { pos.x += dx / scale.current; pos.y += dy / scale.current }
    } else {
      offset.current.x += dx
      offset.current.y += dy
    }
    dragging.current.ox = e.clientX
    dragging.current.oy = e.clientY
    drawCanvas()
  }
  const onMouseUp = () => { dragging.current = { node: null, ox: 0, oy: 0 } }
  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    scale.current = Math.max(0.2, Math.min(3, scale.current * (e.deltaY > 0 ? 0.9 : 1.1)))
    drawCanvas()
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold gradient-text flex items-center gap-3">
              <Share2 className="w-8 h-8 text-primary" />
              Knowledge Graph
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {graphData ? `${graphData.stats.node_count} entidades · ${graphData.stats.edge_count} relações` : 'Entidades e relações extraídas automaticamente'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {sources.length > 1 && (
              <select className="input text-sm" value={selected} onChange={e => setSelected(e.target.value)}>
                {sources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            )}
            <button onClick={handleBuild} disabled={building || !selected} className="btn-primary flex items-center gap-2 text-sm">
              {building ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Share2 className="w-4 h-4" />}
              {building ? 'Construindo...' : graphData ? 'Reconstruir' : 'Construir Grafo'}
            </button>
          </div>
        </div>

        {sources.length === 0 ? (
          <div className="card text-center py-16 text-gray-400">
            <Share2 className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p className="font-medium">Nenhuma fonte conectada</p>
            <p className="text-sm mt-1">Conecte uma fonte em Fontes de Dados primeiro.</p>
          </div>
        ) : loading ? (
          <div className="card flex items-center justify-center py-20">
            <RefreshCw className="w-8 h-8 text-primary animate-spin mr-3" />
            <span className="text-gray-600 dark:text-gray-400">Carregando grafo...</span>
          </div>
        ) : !graphData ? (
          <div className="card text-center py-16">
            <Share2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400 font-medium">Grafo não construído ainda</p>
            <p className="text-sm text-gray-500 mt-1">Clique em "Construir Grafo" para extrair entidades e relações.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Canvas */}
            <div className="lg:col-span-3 space-y-3">
              <div className="card p-3">
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex gap-2 flex-wrap">
                    {Object.entries(graphData.stats.entity_types).map(([type, count]) => (
                      <span key={type} className="text-xs px-2 py-0.5 rounded-full text-white font-medium"
                        style={{ backgroundColor: TYPE_COLORS[type] || '#888' }}>
                        {type} ({count})
                      </span>
                    ))}
                  </div>
                  <div className="ml-auto flex gap-1">
                    <button onClick={() => { scale.current = Math.min(3, scale.current * 1.2); drawCanvas() }}
                      className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500">
                      <ZoomIn className="w-4 h-4" />
                    </button>
                    <button onClick={() => { scale.current = Math.max(0.2, scale.current * 0.8); drawCanvas() }}
                      className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500">
                      <ZoomOut className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <canvas
                  ref={canvasRef}
                  width={800} height={480}
                  className="w-full border border-gray-100 dark:border-gray-700 rounded-lg cursor-grab active:cursor-grabbing bg-gray-50 dark:bg-dark-bg"
                  onMouseDown={onMouseDown}
                  onMouseMove={onMouseMove}
                  onMouseUp={onMouseUp}
                  onMouseLeave={onMouseUp}
                  onWheel={onWheel}
                />
                <p className="text-xs text-gray-400 text-center mt-1">
                  Arraste nós · Scroll para zoom · Clique para detalhes
                </p>
              </div>

              {/* Relation types */}
              <div className="card p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Tipos de Relação</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(graphData.stats.relation_types).map(([type, count]) => (
                    <span key={type} className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-gray-700 dark:text-gray-300">
                      {type} <span className="font-bold">({count})</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-4">
              {/* Search */}
              <div className="card p-4">
                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Buscar Entidade</p>
                <div className="flex gap-2">
                  <input
                    className="input text-sm flex-1"
                    placeholder="Ex: Michelin"
                    value={searchQ}
                    onChange={e => setSearchQ(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSearch()}
                  />
                  <button onClick={handleSearch} className="btn-primary p-2">
                    <Search className="w-4 h-4" />
                  </button>
                </div>
                {searchResults.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {searchResults.slice(0, 8).map((r, i) => (
                      <button
                        key={i}
                        className="w-full text-left text-xs p-2 rounded hover:bg-gray-50 dark:hover:bg-dark-bg flex items-center gap-2"
                        onClick={() => handleNodeClick(r.id)}
                      >
                        <span className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{ backgroundColor: TYPE_COLORS[r.type] || '#888' }} />
                        <span className="font-medium truncate">{r.label}</span>
                        <span className="ml-auto text-gray-400">{r.degree}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Top entities */}
              <div className="card p-4">
                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Top Entidades</p>
                <div className="space-y-1">
                  {graphData.stats.top_entities.slice(0, 8).map((e, i) => (
                    <button
                      key={i}
                      onClick={() => handleNodeClick(e.id)}
                      className={`w-full text-left text-xs p-2 rounded flex items-center gap-2 transition-colors
                        ${activeNode === e.id ? 'bg-primary/10 text-primary' : 'hover:bg-gray-50 dark:hover:bg-dark-bg'}`}
                    >
                      <span className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: TYPE_COLORS[e.type] || '#888' }} />
                      <span className="font-medium truncate flex-1">{e.label}</span>
                      <span className="text-gray-400 flex-shrink-0">deg {e.degree}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Entity detail */}
              {focusEntity && (
                <div className="card p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Info className="w-4 h-4 text-primary" />
                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 truncate">
                      {focusEntity.entity?.label}
                    </p>
                  </div>
                  <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                    <p><span className="font-medium">Tipo:</span> {focusEntity.entity?.type}</p>
                    <p><span className="font-medium">Grau:</span> {focusEntity.entity?.degree}</p>
                    {focusEntity.entity?.frequency > 1 && (
                      <p><span className="font-medium">Freq:</span> {focusEntity.entity.frequency}x</p>
                    )}
                    {focusEntity.entity?.revenue_sum && (
                      <p><span className="font-medium">Receita:</span> R$ {Number(focusEntity.entity.revenue_sum).toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</p>
                    )}
                  </div>
                  {focusEntity.neighbors?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                      <p className="text-xs font-medium text-gray-500 mb-1">
                        Vizinhos ({focusEntity.neighbor_count})
                      </p>
                      <div className="space-y-1">
                        {focusEntity.neighbors.slice(0, 5).map((n: any, i: number) => (
                          <div key={i} className="text-xs flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                              style={{ backgroundColor: TYPE_COLORS[n.type] || '#888' }} />
                            <span className="truncate">{n.label}</span>
                            <span className="ml-auto text-gray-400 flex-shrink-0 text-xs">{n.relation}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
