export default function WelcomeMessage() {
  return (
    <div className="text-center py-12 animate-fade-in">
      <div className="text-6xl mb-4 animate-pulse-slow">🔮</div>
      
      <h1 className="text-4xl font-bold gradient-text mb-2">
        Bem-vindo ao Oráculo
      </h1>
      
      <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
        Seu Consultor de IA para Decisões Estratégicas
      </p>

      <div className="max-w-2xl mx-auto">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
            Como posso ajudá-lo hoje?
          </h3>
          
          <div className="text-left space-y-3 text-gray-600 dark:text-gray-400">
            <div className="flex items-start gap-3">
              <span className="text-xl">📊</span>
              <div>
                <strong className="text-gray-900 dark:text-gray-100">Análise de Dados</strong>
                <p className="text-sm">Faça upload de planilhas e obtenha insights instantâneos</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-xl">🔮</span>
              <div>
                <strong className="text-gray-900 dark:text-gray-100">Análise Preditiva</strong>
                <p className="text-sm">Previsões baseadas em tendências e padrões históricos</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-xl">💡</span>
              <div>
                <strong className="text-gray-900 dark:text-gray-100">Insights Automáticos</strong>
                <p className="text-sm">Detecção proativa de oportunidades e riscos</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <span className="text-xl">🎯</span>
              <div>
                <strong className="text-gray-900 dark:text-gray-100">Recomendações Estratégicas</strong>
                <p className="text-sm">Sugestões acionáveis para melhorar resultados</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
