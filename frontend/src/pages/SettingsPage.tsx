import { Settings, Database, Zap, Shield } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold gradient-text mb-6">
          Configurações
        </h1>

        <div className="space-y-6">
          {/* Sistema */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Settings className="w-6 h-6 text-primary" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Sistema
              </h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    OpenRAG
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Sistema de RAG enterprise-grade
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                  Ativo
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    OpenSearch
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Vector store e busca híbrida
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                  Online
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Langflow
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Workflows visuais de IA
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                  Online
                </span>
              </div>
            </div>
          </div>

          {/* Dados */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Database className="w-6 h-6 text-secondary" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Dados
              </h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Documentos Indexados
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Total de documentos na base de conhecimento
                  </p>
                </div>
                <span className="font-bold text-gray-900 dark:text-gray-100">
                  1,234
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Último Backup
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Backup automático dos dados
                  </p>
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Hoje, 03:00
                </span>
              </div>
            </div>
          </div>

          {/* Performance */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Zap className="w-6 h-6 text-accent" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Performance
              </h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Cache de Embeddings
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Reduz custos em até 50%
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Busca Híbrida
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Vetorial + keyword para melhor precisão
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Reranking
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Melhora qualidade dos resultados
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/40 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Segurança */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-6 h-6 text-green-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Segurança
              </h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Criptografia
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Dados criptografados em repouso
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                  Ativo
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    Auditoria
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Log de todas as ações
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                  Ativo
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
