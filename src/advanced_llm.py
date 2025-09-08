"""
Sistema LLM avançado com RAG (Retrieval-Augmented Generation) para GPTRACKER
"""
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import openai
import pickle
from pathlib import Path
from dotenv import load_dotenv

# Importações condicionais para ML
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ Bibliotecas ML não disponíveis. Funcionando em modo básico.")

# Carregar variáveis de ambiente
load_dotenv()

class AdvancedLLMManager:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = None
        self.vector_store = None
        self.document_store = []
        self.index_path = "vector_index.faiss"
        self.documents_path = "documents.pkl"
        
        # Inicializar modelo de embeddings
        self._init_embedding_model()
        
        # Carregar índice existente se disponível
        self._load_vector_store()
    
    def _init_embedding_model(self):
        """Inicializa modelo de embeddings"""
        if not ML_AVAILABLE:
            print("Modo básico: embeddings não disponíveis")
            self.embedding_model = None
            return
            
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Erro ao carregar modelo de embeddings: {e}")
            self.embedding_model = None
    
    def _load_vector_store(self):
        """Carrega índice vetorial existente"""
        if not ML_AVAILABLE:
            # Em modo básico, apenas carregar documentos se existirem
            try:
                if os.path.exists(self.documents_path):
                    with open(self.documents_path, 'rb') as f:
                        self.document_store = pickle.load(f)
                    print(f"Documentos carregados: {len(self.document_store)} (modo básico)")
            except Exception as e:
                print(f"Erro ao carregar documentos: {e}")
            return
            
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.documents_path):
                self.vector_store = faiss.read_index(self.index_path)
                with open(self.documents_path, 'rb') as f:
                    self.document_store = pickle.load(f)
                print(f"Índice carregado: {len(self.document_store)} documentos")
        except Exception as e:
            print(f"Erro ao carregar índice: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Cria novo índice vetorial"""
        if not ML_AVAILABLE:
            self.document_store = []
            return
            
        if self.embedding_model:
            # Dimensão do modelo all-MiniLM-L6-v2
            dimension = 384
            self.vector_store = faiss.IndexFlatIP(dimension)
            self.document_store = []
    
    def add_documents_to_index(self, documents: List[Dict]):
        """Adiciona documentos ao índice vetorial"""
        if not documents:
            return
            
        # Em modo básico, apenas armazenar documentos sem embeddings
        if not ML_AVAILABLE or not self.embedding_model:
            self.document_store.extend(documents)
            self._save_documents_only()
            return
        
        texts = []
        for doc in documents:
            # Combinar campos relevantes do documento
            text_parts = []
            if 'content' in doc:
                text_parts.append(doc['content'])
            if 'metadata' in doc:
                for key, value in doc['metadata'].items():
                    text_parts.append(f"{key}: {value}")
            
            combined_text = " ".join(text_parts)
            texts.append(combined_text)
            self.document_store.append(doc)
        
        # Gerar embeddings
        embeddings = self.embedding_model.encode(texts)
        
        # Adicionar ao índice FAISS
        self.vector_store.add(embeddings.astype('float32'))
        
        # Salvar índice
        self._save_vector_store()
    
    def _save_documents_only(self):
        """Salva apenas documentos (modo básico)"""
        try:
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.document_store, f)
        except Exception as e:
            print(f"Erro ao salvar documentos: {e}")
    
    def _save_vector_store(self):
        """Salva índice vetorial"""
        try:
            faiss.write_index(self.vector_store, self.index_path)
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.document_store, f)
        except Exception as e:
            print(f"Erro ao salvar índice: {e}")
    
    def search_relevant_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Busca documentos relevantes usando similaridade vetorial ou busca textual básica"""
        if not self.document_store:
            return []
        
        # Se ML não disponível, fazer busca textual simples
        if not ML_AVAILABLE or not self.embedding_model or not self.vector_store:
            return self._simple_text_search(query, top_k)
        
        # Gerar embedding da consulta
        query_embedding = self.embedding_model.encode([query])
        
        # Buscar documentos similares
        scores, indices = self.vector_store.search(query_embedding.astype('float32'), top_k)
        
        relevant_docs = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.document_store):
                doc = self.document_store[idx].copy()
                doc['relevance_score'] = float(score)
                relevant_docs.append(doc)
        
        return relevant_docs
    
    def _simple_text_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Busca textual simples quando ML não está disponível"""
        query_lower = query.lower()
        relevant_docs = []
        
        for doc in self.document_store:
            content = doc.get('content', '').lower()
            # Calcular relevância baseada em palavras-chave
            score = 0
            for word in query_lower.split():
                if word in content:
                    score += content.count(word)
            
            if score > 0:
                doc_copy = doc.copy()
                doc_copy['relevance_score'] = score
                relevant_docs.append(doc_copy)
        
        # Ordenar por relevância e retornar top_k
        relevant_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_docs[:top_k]
    
    def create_knowledge_base_from_data(self, df: pd.DataFrame):
        """Cria base de conhecimento a partir dos dados"""
        if df.empty:
            print("DataFrame vazio - não criando base de conhecimento")
            return
        
        print(f"Criando base de conhecimento com {len(df)} registros")
        print(f"Colunas disponíveis: {list(df.columns)}")
        
        documents = []
        
        # Detectar colunas automaticamente (mais flexível)
        cliente_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['cliente', 'consignatario', 'importador', 'exportador'])]
        quantidade_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['qtd', 'quantidade', 'container', 'teus', 'volumes'])]
        data_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['data', 'mes', 'ano', 'periodo'])]
        
        print(f"Colunas detectadas - Cliente: {cliente_cols}, Quantidade: {quantidade_cols}, Data: {data_cols}")
        
        # Usar primeira coluna encontrada de cada tipo
        cliente_col = cliente_cols[0] if cliente_cols else None
        quantidade_col = quantidade_cols[0] if quantidade_cols else None
        data_col = data_cols[0] if data_cols else None
        
        # Criar documentos gerais dos dados
        for idx, row in df.iterrows():
            content_parts = []
            metadata = {}
            
            for col, value in row.items():
                if pd.notna(value):
                    content_parts.append(f"{col}: {value}")
                    metadata[col] = value
            
            if content_parts:
                documents.append({
                    'type': 'data_record',
                    'content': " | ".join(content_parts),
                    'metadata': metadata
                })
        
        # Criar resumos por cliente se detectado
        if cliente_col and quantidade_col:
            try:
                # Converter coluna de quantidade para numérico
                df[quantidade_col] = pd.to_numeric(df[quantidade_col], errors='coerce')
                
                client_summaries = df.groupby(cliente_col).agg({
                    quantidade_col: ['sum', 'count', 'mean']
                }).reset_index()
                
                for _, row in client_summaries.iterrows():
                    cliente = row[cliente_col]
                    total = row[(quantidade_col, 'sum')]
                    count = row[(quantidade_col, 'count')]
                    media = row[(quantidade_col, 'mean')]
                    
                    content = f"Cliente: {cliente} | Total: {total} | Operações: {count} | Média: {media:.2f}"
                    
                    documents.append({
                        'type': 'client_summary',
                        'content': content,
                        'metadata': {
                            'cliente': cliente,
                            'total': total,
                            'operacoes': count
                        }
                    })
            except Exception as e:
                print(f"Erro ao criar resumos por cliente: {e}")
        
        # Criar resumos por período se detectado
        if data_col and quantidade_col:
            try:
                period_summaries = df.groupby(data_col).agg({
                    quantidade_col: 'sum'
                }).reset_index()
                
                for _, row in period_summaries.iterrows():
                    periodo = row[data_col]
                    total = row[quantidade_col]
                    
                    content = f"Período: {periodo} | Total: {total}"
                    
                    documents.append({
                        'type': 'period_summary',
                        'content': content,
                        'metadata': {
                            'periodo': periodo,
                            'total': total
                        }
                    })
            except Exception as e:
                print(f"Erro ao criar resumos por período: {e}")
        
        print(f"Total de documentos criados: {len(documents)}")
        
        # Adicionar documentos ao índice
        if documents:
            self.add_documents_to_index(documents)
        else:
            print("Nenhum documento foi criado!")
    
    def generate_enhanced_response(self, query: str, df: pd.DataFrame, max_tokens: int = 1000) -> str:
        """Gera resposta usando RAG com GPT-4"""
        try:
            # Buscar documentos relevantes
            relevant_docs = self.search_relevant_documents(query, top_k=5)
            
            # Construir contexto detalhado
            context_parts = []
            
            # Adicionar dados relevantes da base de conhecimento
            if relevant_docs:
                context_parts.append("=== DADOS DA BASE DE CONHECIMENTO ===")
                for i, doc in enumerate(relevant_docs, 1):
                    context_parts.append(f"{i}. {doc['content']}")
                    if 'relevance_score' in doc:
                        context_parts.append(f"   (Relevância: {doc['relevance_score']:.2f})")
            
            # Análise detalhada do DataFrame atual
            if not df.empty:
                context_parts.append("\n=== ANÁLISE DOS DADOS ATUAIS ===")
                
                # Informações básicas
                context_parts.append(f"Total de registros: {len(df):,}")
                context_parts.append(f"Colunas disponíveis: {', '.join(df.columns)}")
                
                # Detectar e analisar colunas automaticamente
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['data', 'mes', 'ano', 'periodo'])]
                client_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['cliente', 'consignatario', 'importador', 'exportador'])]
                quantity_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['qtd', 'quantidade', 'container', 'teus', 'volumes'])]
                
                # Estatísticas por colunas de quantidade
                if quantity_cols:
                    for col in quantity_cols:
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            total = df[col].sum()
                            media = df[col].mean()
                            context_parts.append(f"\n{col.upper()}:")
                            context_parts.append(f"  - Total: {total:,.0f}")
                            context_parts.append(f"  - Média: {media:,.2f}")
                            context_parts.append(f"  - Registros válidos: {df[col].notna().sum():,}")
                        except:
                            continue
                
                # Top clientes se disponível
                if client_cols and quantity_cols:
                    try:
                        client_col = client_cols[0]
                        qty_col = quantity_cols[0]
                        top_clients = df.groupby(client_col)[qty_col].sum().sort_values(ascending=False).head(5)
                        context_parts.append(f"\nTOP 5 CLIENTES por {qty_col}:")
                        for i, (client, value) in enumerate(top_clients.items(), 1):
                            context_parts.append(f"  {i}. {client}: {value:,.0f}")
                    except:
                        pass
                
                # Análise temporal se disponível
                if date_cols and quantity_cols:
                    try:
                        date_col = date_cols[0]
                        qty_col = quantity_cols[0]
                        temporal_data = df.groupby(date_col)[qty_col].sum().sort_index()
                        if len(temporal_data) > 1:
                            context_parts.append(f"\nTENDÊNCIA TEMPORAL por {date_col}:")
                            for period, value in temporal_data.tail(5).items():
                                context_parts.append(f"  {period}: {value:,.0f}")
                            
                            # Calcular tendência
                            if len(temporal_data) >= 2:
                                last_value = temporal_data.iloc[-1]
                                prev_value = temporal_data.iloc[-2]
                                change = last_value - prev_value
                                pct_change = (change / prev_value * 100) if prev_value != 0 else 0
                                context_parts.append(f"  Variação último período: {change:+,.0f} ({pct_change:+.1f}%)")
                    except:
                        pass
                
                # Responder perguntas específicas baseadas na query
                context_parts.append(f"\n=== ANÁLISE ESPECÍFICA PARA A PERGUNTA ===")
                context_parts.append(self._analyze_specific_query(query, df))
            
            context = "\n".join(context_parts)
            
            # Criar prompt aprimorado
            system_prompt = """
            Você é o GPTRACKER, um assistente de IA especializado em análise de dados logísticos e comerciais da Itracker.
            
            Suas responsabilidades:
            - Analisar dados de importação, exportação e cabotagem
            - Fornecer insights comerciais e operacionais detalhados
            - Identificar oportunidades de negócio com base em dados reais
            - Responder perguntas sobre performance e metas com números precisos
            
            Diretrizes OBRIGATÓRIAS de resposta:
            - SEMPRE use números específicos e dados reais fornecidos no contexto
            - SEMPRE cite as fontes dos dados (ex: "Baseado nos dados analisados...")
            - SEMPRE forneça análises quantitativas detalhadas
            - SEMPRE inclua comparações, tendências e insights acionáveis
            - NUNCA dê respostas genéricas sem dados específicos
            - Se não houver dados suficientes, seja específico sobre o que está faltando
            - Formate números com separadores de milhares (ex: 1.234 containers)
            - Inclua percentuais e variações quando relevante
            """
            
            user_prompt = f"""
            Pergunta: {query}
            
            Contexto disponível:
            {context}
            
            Por favor, forneça uma resposta completa e útil baseada nas informações disponíveis.
            """
            
            # Chamar GPT-4 Turbo
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Erro ao gerar resposta: {str(e)}"
    
    def _analyze_specific_query(self, query: str, df: pd.DataFrame) -> str:
        """Analisa a query específica e retorna insights direcionados"""
        query_lower = query.lower()
        insights = []
        
        try:
            # Detectar colunas automaticamente
            client_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['cliente', 'consignatario', 'importador', 'exportador'])]
            quantity_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['qtd', 'quantidade', 'container', 'teus', 'volumes'])]
            date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['data', 'mes', 'ano', 'periodo'])]
            port_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['porto', 'port', 'terminal'])]
            armador_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['armador', 'shipping', 'carrier'])]
            
            # Análise por cliente específico
            if any(word in query_lower for word in ['cliente', 'consignatario', 'accumed']) and client_cols:
                client_col = client_cols[0]
                if 'accumed' in query_lower:
                    accumed_data = df[df[client_col].str.contains('ACCUMED', case=False, na=False)]
                    if not accumed_data.empty and quantity_cols:
                        qty_col = quantity_cols[0]
                        total = accumed_data[qty_col].sum()
                        insights.append(f"ACCUMED: {total:,.0f} {qty_col} encontrados nos dados")
                        
                        if date_cols:
                            date_col = date_cols[0]
                            by_period = accumed_data.groupby(date_col)[qty_col].sum()
                            insights.append(f"Distribuição por período: {dict(by_period)}")
            
            # Análise temporal específica
            if any(word in query_lower for word in ['março', 'march', '2025', '2024']) and date_cols and quantity_cols:
                date_col = date_cols[0]
                qty_col = quantity_cols[0]
                
                if 'março' in query_lower or 'march' in query_lower:
                    march_data = df[df[date_col].astype(str).str.contains('03|março|march', case=False, na=False)]
                    if not march_data.empty:
                        total = march_data[qty_col].sum()
                        insights.append(f"Março: {total:,.0f} {qty_col}")
                
                if '2025' in query_lower:
                    data_2025 = df[df[date_col].astype(str).str.contains('2025', na=False)]
                    if not data_2025.empty:
                        total = data_2025[qty_col].sum()
                        insights.append(f"2025: {total:,.0f} {qty_col}")
                
                if '2024' in query_lower:
                    data_2024 = df[df[date_col].astype(str).str.contains('2024', na=False)]
                    if not data_2024.empty:
                        total = data_2024[qty_col].sum()
                        insights.append(f"2024: {total:,.0f} {qty_col}")
            
            # Análise por porto
            if any(word in query_lower for word in ['porto', 'santos', 'port']) and port_cols and quantity_cols:
                port_col = port_cols[0]
                qty_col = quantity_cols[0]
                
                if 'santos' in query_lower:
                    santos_data = df[df[port_col].str.contains('SANTOS', case=False, na=False)]
                    if not santos_data.empty:
                        total = santos_data[qty_col].sum()
                        insights.append(f"Porto de Santos: {total:,.0f} {qty_col}")
                        
                        if armador_cols:
                            armador_col = armador_cols[0]
                            top_armadores = santos_data.groupby(armador_col)[qty_col].sum().sort_values(ascending=False).head(5)
                            insights.append(f"Top armadores Santos: {dict(top_armadores)}")
            
            # Análise comparativa
            if any(word in query_lower for word in ['compare', 'comparar', 'janeiro', 'fevereiro']) and date_cols and quantity_cols:
                date_col = date_cols[0]
                qty_col = quantity_cols[0]
                
                jan_data = df[df[date_col].astype(str).str.contains('01|janeiro|january', case=False, na=False)]
                feb_data = df[df[date_col].astype(str).str.contains('02|fevereiro|february', case=False, na=False)]
                
                if not jan_data.empty and not feb_data.empty:
                    jan_total = jan_data[qty_col].sum()
                    feb_total = feb_data[qty_col].sum()
                    diff = feb_total - jan_total
                    pct_change = (diff / jan_total * 100) if jan_total != 0 else 0
                    
                    insights.append(f"Janeiro: {jan_total:,.0f} {qty_col}")
                    insights.append(f"Fevereiro: {feb_total:,.0f} {qty_col}")
                    insights.append(f"Variação: {diff:+,.0f} ({pct_change:+.1f}%)")
            
            # Análise de tendência
            if any(word in query_lower for word in ['tendencia', 'trend', 'ultimos', 'meses']) and date_cols and quantity_cols:
                date_col = date_cols[0]
                qty_col = quantity_cols[0]
                
                monthly_data = df.groupby(date_col)[qty_col].sum().sort_index().tail(3)
                if len(monthly_data) >= 2:
                    insights.append(f"Últimos 3 meses: {dict(monthly_data)}")
                    
                    # Calcular tendência
                    values = monthly_data.values
                    if len(values) >= 2:
                        trend = values[-1] - values[0]
                        insights.append(f"Tendência geral: {trend:+,.0f} {qty_col}")
            
            return "\n".join(insights) if insights else "Análise específica não disponível para esta consulta"
            
        except Exception as e:
            return f"Erro na análise específica: {str(e)}"
    
    def generate_proactive_insights(self, df: pd.DataFrame) -> List[str]:
        """Gera insights proativos baseados nos dados"""
        insights = []
        
        if df.empty:
            return insights
        
        try:
            # Análise de tendências
            if 'ano_mes' in df.columns and len(df['ano_mes'].unique()) >= 3:
                monthly_data = df.groupby('ano_mes')['qtd_container'].sum()
                recent_months = monthly_data.tail(3)
                
                if len(recent_months) >= 2:
                    trend = recent_months.iloc[-1] - recent_months.iloc[-2]
                    if trend > 0:
                        insights.append(f"📈 Crescimento de {trend:,.0f} containers no último mês")
                    elif trend < 0:
                        insights.append(f"📉 Redução de {abs(trend):,.0f} containers no último mês")
            
            # Top performers
            if 'cliente' in df.columns:
                top_client = df.groupby('cliente')['qtd_container'].sum().idxmax()
                top_volume = df.groupby('cliente')['qtd_container'].sum().max()
                insights.append(f"🏆 Top cliente: {top_client} ({top_volume:,.0f} containers)")
            
            # Oportunidades sazonais
            if 'mes' in df.columns:
                monthly_avg = df.groupby('mes')['qtd_container'].mean()
                if not monthly_avg.empty:
                    best_month = monthly_avg.idxmax()
                    insights.append(f"🌟 Melhor mês histórico: {best_month} (média: {monthly_avg[best_month]:,.0f})")
            
        except Exception as e:
            insights.append(f"Erro ao gerar insights: {str(e)}")
        
        return insights
    
    def generate_response(self, query: str, context: str = "", conversation_history: List[Dict] = None, df: pd.DataFrame = None) -> str:
        """Método principal para gerar respostas do chat com dados integrados"""
        try:
            # Se temos dados, usar o método enhanced que inclui análise detalhada
            if df is not None and not df.empty:
                return self.generate_enhanced_response(query, df)
            
            # Fallback para método básico quando não há dados
            messages = [
                {
                    "role": "system",
                    "content": """Você é o GPTRACKER, um assistente especializado em análise de dados logísticos e comerciais da empresa Itracker.

IMPORTANTE: Atualmente não há dados carregados no sistema. Para fornecer análises precisas, é necessário:
1. Carregar planilhas de dados via upload ou links da nuvem
2. Aguardar o processamento dos dados
3. Refazer a pergunta para obter análise baseada em dados reais

Suas especialidades incluem:
- Análise de dados de importação, exportação e cabotagem
- Insights sobre performance comercial e oportunidades
- Análise de budget e metas
- Tendências do mercado logístico

Quando não há dados disponíveis, explique claramente essa limitação e oriente sobre como carregar dados."""
                }
            ]
            
            # Adicionar histórico de conversa (últimas 5 mensagens)
            if conversation_history:
                for msg in conversation_history[-5:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Adicionar contexto se fornecido
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Contexto adicional: {context}"
                })
            
            # Adicionar pergunta atual
            messages.append({
                "role": "user",
                "content": query
            })
            
            # Gerar resposta usando OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Erro ao gerar resposta: {str(e)}"
    
    def update_knowledge_base(self, df: pd.DataFrame):
        """Atualiza base de conhecimento com novos dados"""
        # Limpar índice existente
        self._create_new_index()
        
        # Recriar base de conhecimento
        self.create_knowledge_base_from_data(df)
        
        print(f"Base de conhecimento atualizada com {len(self.document_store)} documentos")

# Instância global
advanced_llm = AdvancedLLMManager()
