import { BarChart3, TrendingUp, Users, Package } from 'lucide-react'

export default function AnalyticsPage() {
  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold gradient-text mb-6">
          Analytics Dashboard
        </h1>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400">
                Total Containers
              </h3>
              <Package className="w-5 h-5 text-primary" />
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              1,234
            </p>
            <p className="text-sm text-green-500 mt-2">
              +23% vs mês anterior
            </p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400">
                Clientes Ativos
              </h3>
              <Users className="w-5 h-5 text-secondary" />
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              45
            </p>
            <p className="text-sm text-green-500 mt-2">
              +5 novos clientes
            </p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400">
                Crescimento
              </h3>
              <TrendingUp className="w-5 h-5 text-accent" />
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              23%
            </p>
            <p className="text-sm text-green-500 mt-2">
              Tendência positiva
            </p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400">
                Insights Gerados
              </h3>
              <BarChart3 className="w-5 h-5 text-yellow-500" />
            </div>
            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              12
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Este mês
            </p>
          </div>
        </div>

        {/* Placeholder for Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
              Volume por Mês
            </h3>
            <div className="h-64 flex items-center justify-center text-gray-400">
              <p>Gráfico será implementado com dados reais</p>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
              Top Clientes
            </h3>
            <div className="h-64 flex items-center justify-center text-gray-400">
              <p>Gráfico será implementado com dados reais</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
