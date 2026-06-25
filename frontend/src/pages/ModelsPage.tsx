import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Cpu, Check, ArrowLeft, Sparkles } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

interface Model {
  id: string
  name: string
  is_free: boolean
}

function getAuthHeaders() {
  const token = localStorage.getItem('access_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function ModelsPage() {
  const navigate = useNavigate()
  const [models, setModels] = useState<Model[]>([])
  const [activeModel, setActiveModel] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [selecting, setSelecting] = useState<string | null>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [modelsResp, activeResp] = await Promise.all([
        axios.get(`${API_BASE}/models?provider=zai`, { headers: getAuthHeaders() }),
        axios.get(`${API_BASE}/active-model`, { headers: getAuthHeaders() }),
      ])
      setModels(modelsResp.data.models.filter((m: Model) => m.is_free))
      setActiveModel(activeResp.data.active_model)
    } catch (e) {
      toast.error('Erro ao carregar modelos.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSelect = async (id: string) => {
    setSelecting(id)
    try {
      await axios.post(
        `${API_BASE}/active-model`,
        { model: id },
        { headers: getAuthHeaders() },
      )
      setActiveModel(id)
      toast.success(`Modelo ativo: ${id}`)
    } catch (e) {
      toast.error('Erro ao selecionar modelo.')
    } finally {
      setSelecting(null)
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
        <div>
          <h1 className="text-3xl font-bold gradient-text">Modelos Z.AI</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Modelos gratuitos disponíveis no momento.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {models.map((model) => {
            const isActive = activeModel === model.id
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
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
                        Pago
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
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          Nenhum modelo encontrado com o filtro atual.
        </div>
      )}
    </div>
  )
}
