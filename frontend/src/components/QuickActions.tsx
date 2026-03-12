import { TrendingUp, AlertTriangle, Target, BarChart } from 'lucide-react'

interface QuickActionsProps {
  onSelect: (question: string) => void
}

const quickQuestions = [
  {
    icon: BarChart,
    label: 'Análise do Último Mês',
    question: 'Quantos containers foram movimentados no último mês?',
    color: 'text-blue-500',
  },
  {
    icon: TrendingUp,
    label: 'Tendências de Crescimento',
    question: 'Quais são as principais tendências de crescimento que você identifica?',
    color: 'text-green-500',
  },
  {
    icon: AlertTriangle,
    label: 'Riscos e Oportunidades',
    question: 'Identifique riscos e oportunidades nos dados atuais',
    color: 'text-yellow-500',
  },
  {
    icon: Target,
    label: 'Previsão de Demanda',
    question: 'Qual é a previsão de demanda para o próximo trimestre?',
    color: 'text-purple-500',
  },
]

export default function QuickActions({ onSelect }: QuickActionsProps) {
  return (
    <div className="max-w-4xl mx-auto">
      <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-4">
        💬 Perguntas Sugeridas
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {quickQuestions.map((item, index) => {
          const Icon = item.icon
          return (
            <button
              key={index}
              onClick={() => onSelect(item.question)}
              className="card text-left hover:scale-105 transition-transform group"
            >
              <div className="flex items-start gap-3">
                <Icon className={`w-5 h-5 ${item.color} flex-shrink-0 mt-0.5`} />
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1 group-hover:text-primary transition-colors">
                    {item.label}
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {item.question}
                  </p>
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
