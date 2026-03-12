# 📖 Manual do Usuário - GPTRACKER

## 🎯 Visão Geral

O **GPTRACKER** é sua ferramenta inteligente para análise de dados comerciais e logísticos. Este manual te guiará através de todas as funcionalidades do sistema.

## 🚪 Acesso ao Sistema

### Login Inicial
1. Abra seu navegador e acesse `http://localhost:8501`
2. Use suas credenciais de acesso
3. Selecione "Lembrar-me" para permanecer logado

### Perfis de Usuário

| Perfil | Acesso | Funcionalidades |
|--------|--------|-----------------|
| **Admin** | Total | Todas as funcionalidades |
| **Comercial** | Comercial + Analytics | Dashboard, Chat, Budget, Analytics |
| **Operacional** | Operacional | Dashboard, Chat, Analytics (somente leitura) |

## 🏠 Navegação Principal

### Sidebar (Menu Lateral)
- **🏠 Dashboard**: Visão geral e KPIs
- **💬 Chat GPT**: Conversa inteligente com seus dados
- **📊 Analytics**: Análises avançadas e previsões
- **🎯 Budget & Metas**: Gestão de metas e acompanhamento
- **📁 Gestão de Dados**: Upload e processamento de arquivos
- **🔒 Segurança**: Auditoria e relatórios de segurança

## 📊 Dashboard Executivo

### KPIs Principais
- **Total de Containers**: Quantidade total movimentada
- **Operações**: Número de operações realizadas
- **Clientes Únicos**: Quantidade de clientes ativos
- **Período**: Filtros de data para análise

### Performance vs Budget
- **Gauges Visuais**: Indicadores de performance
- **Cores**: Verde (meta atingida), Amarelo (atenção), Vermelho (abaixo da meta)
- **Percentuais**: Mostra % de atingimento das metas

### Gráficos Interativos
- **Tendências Temporais**: Evolução ao longo do tempo
- **Distribuição por Operação**: Breakdown por tipo
- **Top Clientes**: Ranking dos principais clientes

## 💬 Chat GPT Inteligente

### Como Fazer Perguntas

#### Exemplos de Perguntas Básicas
```
"Quantos containers a Michelin movimentou em 2024?"
"Qual foi a receita total de janeiro?"
"Quem são os top 5 clientes?"
"Mostre a evolução mensal de containers"
```

#### Perguntas Avançadas
```
"Compare a performance de 2024 vs 2023"
"Quais clientes estão abaixo da meta?"
"Identifique oportunidades de upsell"
"Preveja a demanda para os próximos 3 meses"
```

### Recursos do Chat
- **Contexto**: O chat lembra da conversa anterior
- **Insights Proativos**: Sugestões automáticas baseadas nos dados
- **Gráficos**: Visualizações geradas automaticamente
- **Exportação**: Salve respostas importantes

### Dicas para Melhores Resultados
1. **Seja específico**: "Containers da Michelin em janeiro 2024"
2. **Use filtros**: "Exportação no Porto de Santos"
3. **Peça comparações**: "Compare Q1 vs Q2"
4. **Solicite insights**: "O que posso melhorar?"

## 📈 Analytics Avançadas

### Análises Preditivas
- **Previsão de Demanda**: Projeções baseadas em histórico
- **Análise de Sazonalidade**: Identificação de padrões temporais
- **Oportunidades de Crescimento**: Clientes com potencial

### Customer Lifetime Value (CLV)
- **Valor do Cliente**: Receita projetada por cliente
- **Segmentação**: Classificação por valor e potencial
- **Recomendações**: Ações sugeridas por segmento

### Insights Comerciais
- **Tendências de Mercado**: Análise de crescimento/declínio
- **Performance por Segmento**: Comparação entre áreas
- **Alertas Automáticos**: Notificações de desvios importantes

## 🎯 Budget & Metas

### Definindo Metas

#### Meta Anual
1. Acesse "Budget & Metas"
2. Clique em "Definir Meta Anual"
3. Insira:
   - Ano
   - Meta de Receita
   - Meta de Containers
   - Observações (opcional)

#### Meta Mensal
1. Selecione "Meta Mensal"
2. Escolha o período (YYYY-MM)
3. Defina valores específicos
4. Salve a configuração

#### Meta por Cliente
1. Vá para "Meta por Cliente"
2. Selecione o cliente
3. Defina período e valores
4. Configure alertas (opcional)

### Acompanhamento de Performance
- **Gauges de Performance**: Visualização em tempo real
- **Gráficos de Tendência**: Evolução vs meta
- **Relatórios Detalhados**: Breakdown por período/cliente
- **Alertas**: Notificações automáticas de desvios

## 📁 Gestão de Dados

### Upload de Arquivos

#### Formatos Suportados
- Excel (.xlsx, .xls)
- CSV (.csv)
- JSON (.json)
- Parquet (.parquet)

#### Processo de Upload
1. Acesse "Gestão de Dados"
2. Clique em "Upload de Arquivo"
3. Selecione o arquivo
4. Aguarde o processamento automático
5. Verifique o relatório de validação

### Tipos de Dados

#### Dados Logísticos
**Colunas obrigatórias:**
- `qtd_container`: Quantidade de containers
- `cliente`: Nome do cliente
- `ano_mes`: Período (formato YYYYMM)

**Colunas opcionais:**
- `tipo_operacao`: Importação/Exportação/Cabotage
- `porto`: Porto de origem/destino
- `armador`: Empresa armadora
- `navio`: Nome da embarcação

#### Dados Comerciais
**Colunas obrigatórias:**
- `cliente`: Nome do cliente
- `receita`: Valor da receita
- `periodo`: Período (formato YYYYMM)

**Colunas opcionais:**
- `vendedor`: Responsável pela venda
- `regiao`: Região geográfica
- `produto`: Tipo de produto/serviço

#### Dados de Budget
**Colunas obrigatórias:**
- `periodo`: Período da meta
- `meta_receita`: Valor da meta de receita
- `meta_containers`: Meta de containers

#### Dados de Oportunidades
**Colunas obrigatórias:**
- `cliente`: Cliente da oportunidade
- `valor_estimado`: Valor potencial
- `probabilidade`: % de chance de fechamento
- `data_fechamento`: Data prevista

### Validação Automática
- **Verificação de Formato**: Colunas obrigatórias
- **Qualidade dos Dados**: Valores inconsistentes
- **Duplicatas**: Identificação automática
- **Relatório**: Resumo do processamento

## 🔒 Segurança e Auditoria

### Relatórios de Segurança
- **Log de Acessos**: Quem acessou quando
- **Ações Realizadas**: Histórico de modificações
- **Tentativas de Login**: Sucessos e falhas
- **Integridade dos Dados**: Verificações automáticas

### Backup e Recuperação
- **Backup Automático**: Executado diariamente
- **Backup Manual**: Disponível sob demanda
- **Restauração**: Processo guiado de recuperação

### Controle de Acesso
- **Permissões por Módulo**: Controle granular
- **Sessões Ativas**: Visualização de usuários online
- **Expiração de Sessão**: Logout automático por inatividade

## 🔧 Configurações Avançadas

### Personalização do Dashboard
1. Acesse "Configurações" no menu do usuário
2. Selecione "Dashboard"
3. Escolha KPIs a exibir
4. Configure cores e layouts
5. Salve as preferências

### Alertas e Notificações
- **Alertas de Meta**: Quando performance < 80%
- **Novos Dados**: Quando arquivos são processados
- **Anomalias**: Detecção automática de outliers
- **Relatórios Agendados**: Envio automático por email

### Exportação de Dados
- **Relatórios PDF**: Dashboards e análises
- **Excel**: Dados filtrados e processados
- **CSV**: Para integração com outros sistemas
- **API**: Acesso programático via REST

## 📱 Dicas de Uso

### Melhores Práticas
1. **Mantenha dados atualizados**: Upload regular de arquivos
2. **Configure metas realistas**: Use histórico como base
3. **Monitore alertas**: Ação rápida em desvios
4. **Use o chat**: Explore insights com perguntas
5. **Revise relatórios**: Análise semanal de performance

### Atalhos Úteis
- `Ctrl + /`: Abrir chat rapidamente
- `Ctrl + D`: Ir para dashboard
- `Ctrl + U`: Upload de arquivo
- `F5`: Atualizar dados
- `Esc`: Fechar modais

### Resolução de Problemas

#### "Dados não aparecem"
1. Verifique se o arquivo foi processado com sucesso
2. Confirme formato das colunas obrigatórias
3. Verifique filtros aplicados no dashboard

#### "Chat não responde adequadamente"
1. Seja mais específico na pergunta
2. Verifique se há dados para o período solicitado
3. Tente reformular a pergunta

#### "Performance lenta"
1. Reduza o período de análise
2. Limite filtros a dados essenciais
3. Feche abas desnecessárias do navegador

## 📞 Suporte

### Canais de Ajuda
- **Chat Interno**: Use o chat para dúvidas sobre dados
- **Documentação**: Consulte README.md para detalhes técnicos
- **Logs**: Verifique logs de erro em caso de problemas

### Informações para Suporte
Ao solicitar ajuda, forneça:
- Usuário e perfil
- Ação que estava realizando
- Mensagem de erro (se houver)
- Horário do problema
- Navegador utilizado

---

## 🎓 Treinamento Rápido

### Primeiros 15 Minutos
1. **Login** e exploração da interface
2. **Dashboard** - entenda os KPIs principais
3. **Chat** - faça uma pergunta simples sobre seus dados

### Primeira Semana
1. **Configure metas** para seu período atual
2. **Carregue dados** adicionais se disponível
3. **Explore analytics** para entender tendências
4. **Configure alertas** para acompanhamento

### Primeiro Mês
1. **Análise completa** de performance vs budget
2. **Identificação de oportunidades** comerciais
3. **Uso avançado do chat** para insights estratégicos
4. **Configuração de relatórios** automáticos

---

**GPTRACKER** - Sua inteligência comercial em ação! 🚀

*Para dúvidas técnicas, consulte o Guia de Instalação ou README.md*
