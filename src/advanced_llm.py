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
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from pathlib import Path
from dotenv import load_dotenv

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
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Erro ao carregar modelo de embeddings: {e}")
            self.embedding_model = None
    
    def _load_vector_store(self):
        """Carrega índice vetorial existente"""
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
        if self.embedding_model:
            # Dimensão do modelo all-MiniLM-L6-v2
            dimension = 384
            self.vector_store = faiss.IndexFlatIP(dimension)
            self.document_store = []
    
    def add_documents_to_index(self, documents: List[Dict]):
        """Adiciona documentos ao índice vetorial"""
        if not self.embedding_model or not documents:
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
    
    def _save_vector_store(self):
        """Salva índice vetorial"""
        try:
            faiss.write_index(self.vector_store, self.index_path)
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.document_store, f)
        except Exception as e:
            print(f"Erro ao salvar índice: {e}")
    
    def search_relevant_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Busca documentos relevantes usando similaridade vetorial"""
        if not self.embedding_model or not self.vector_store:
            return []
        
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
            relevant_docs = self.search_relevant_documents(query, top_k=3)
            
            # Construir contexto
            context_parts = []
            
            # Adicionar dados relevantes
            if relevant_docs:
                context_parts.append("Informações relevantes da base de conhecimento:")
                for doc in relevant_docs:
                    context_parts.append(f"- {doc['content']}")
            
            # Adicionar estatísticas gerais
            if not df.empty:
                total_containers = df['qtd_container'].sum()
                total_clientes = df['cliente'].nunique() if 'cliente' in df.columns else 0
                
                context_parts.append(f"\nEstatísticas gerais:")
                context_parts.append(f"- Total de containers: {total_containers:,}")
                context_parts.append(f"- Número de clientes únicos: {total_clientes}")
            
            context = "\n".join(context_parts)
            
            # Criar prompt aprimorado
            system_prompt = """
            Você é o GPTRACKER, um assistente de IA especializado em análise de dados logísticos e comerciais da Itracker.
            
            Suas responsabilidades:
            - Analisar dados de importação, exportação e cabotagem
            - Fornecer insights comerciais e operacionais
            - Identificar oportunidades de negócio
            - Responder perguntas sobre performance e metas
            
            Diretrizes de resposta:
            - Seja preciso e use números específicos quando disponíveis
            - Forneça insights acionáveis
            - Mantenha tom profissional mas acessível
            - Destaque tendências e padrões importantes
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
    
    def generate_response(self, query: str, context: str = "", conversation_history: List[Dict] = None) -> str:
        """Método principal para gerar respostas do chat"""
        try:
            # Preparar mensagens para o chat
            messages = [
                {
                    "role": "system",
                    "content": """Você é o GPTRACKER, um assistente especializado em análise de dados logísticos e comerciais da empresa Itracker.

Suas especialidades incluem:
- Análise de dados de importação, exportação e cabotagem
- Insights sobre performance comercial e oportunidades
- Análise de budget e metas
- Tendências do mercado logístico

Responda de forma clara, objetiva e profissional. Use dados quando disponível e forneça insights acionáveis."""
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
