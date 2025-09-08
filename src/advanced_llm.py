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
import logging

# Configurar logger do módulo
logger = logging.getLogger(__name__)

# Importações condicionais para ML
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.getLogger(__name__).debug("Bibliotecas ML não disponíveis. Funcionando em modo básico.")

# Carregar variáveis de ambiente
load_dotenv()
logger = logging.getLogger(__name__)

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
            logger.debug("Modo básico: embeddings não disponíveis")
            self.embedding_model = None
            return
            
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Erro ao carregar modelo de embeddings: {e}")
            self.embedding_model = None
    
    def _load_vector_store(self):
        """Carrega índice vetorial existente"""
        if not ML_AVAILABLE:
            # Em modo básico, apenas carregar documentos se existirem
            try:
                if os.path.exists(self.documents_path):
                    with open(self.documents_path, 'rb') as f:
                        self.document_store = pickle.load(f)
                    logger.debug(f"Documentos carregados: {len(self.document_store)} (modo básico)")
            except Exception as e:
                logger.warning(f"Erro ao carregar documentos: {e}")
            return
            
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.documents_path):
                self.vector_store = faiss.read_index(self.index_path)
                with open(self.documents_path, 'rb') as f:
                    self.document_store = pickle.load(f)
                logger.debug(f"Índice carregado: {len(self.document_store)} documentos")
        except Exception as e:
            logger.warning(f"Erro ao carregar índice: {e}")
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
            logger.error(f"Erro ao salvar documentos: {e}")
    
    def _save_vector_store(self):
        """Salva índice vetorial"""
        try:
            faiss.write_index(self.vector_store, self.index_path)
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.document_store, f)
        except Exception as e:
            logger.error(f"Erro ao salvar índice: {e}")
    
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
            logger.debug("DataFrame vazio - não criando base de conhecimento")
            return
        
        logger.debug(f"Criando base de conhecimento com {len(df)} registros")
        logger.debug(f"Colunas disponíveis: {list(df.columns)}")
        
        documents = []
        
        # Detectar colunas automaticamente (mais flexível)
        cliente_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['cliente', 'consignatario', 'importador', 'exportador'])]
        quantidade_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['qtd', 'quantidade', 'container', 'teus', 'volumes'])]
        data_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['data', 'mes', 'ano', 'periodo'])]
        
        logger.debug(f"Colunas detectadas - Cliente: {cliente_cols}, Quantidade: {quantidade_cols}, Data: {data_cols}")
        
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
                logger.warning(f"Erro ao criar resumos por cliente: {e}")
        
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
                logger.warning(f"Erro ao criar resumos por período: {e}")
        
        logger.debug(f"Total de documentos criados: {len(documents)}")
        
        # Adicionar documentos ao índice
        if documents:
            self.add_documents_to_index(documents)
        else:
            logger.debug("Nenhum documento foi criado!")
    
    def generate_enhanced_response(self, query: str, df: pd.DataFrame, max_tokens: int = 1000) -> str:
        """Gera resposta usando RAG com GPT-4"""
        try:
            # Buscar documentos relevantes
            relevant_docs = self.search_relevant_documents(query, top_k=5)
            
            # Construir contexto detalhado (priorizando o DataFrame consolidado)
            context_parts = []
            
            # Análise detalhada do DataFrame atual (fonte canônica)
            if not df.empty:
                context_parts.append("\n=== ANÁLISE DETALHADA DOS DADOS (FONTE CANÔNICA) ===")
                
                # Informações básicas
                context_parts.append(f"Total de registros: {len(df):,}")
                context_parts.append(f"Total de colunas: {len(df.columns)}")
                
                # Análise detalhada de cada coluna
                context_parts.append("\n--- ESTRUTURA DAS COLUNAS ---")
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    non_null = df[col].notna().sum()
                    unique_vals = df[col].nunique()
                    
                    # Mostrar alguns valores únicos para entender o conteúdo
                    sample_values = df[col].dropna().unique()[:5]
                    sample_str = ", ".join([str(v) for v in sample_values])
                    
                    context_parts.append(f"{col}: {dtype} | {non_null:,} valores | {unique_vals:,} únicos | Ex: {sample_str}")
                
                # Detectar colunas por categoria
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['data', 'mes', 'mês', 'ano', 'periodo', 'ano/mes', 'ano_mes'])]
                client_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['cliente', 'consignatario', 'importador', 'exportador'])]
                quantity_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['qtd', 'quantidade', 'container', 'teus', 'volumes'])]
                
                context_parts.append(f"\n--- CATEGORIZAÇÃO AUTOMÁTICA ---")
                context_parts.append(f"Colunas numéricas: {numeric_cols}")
                context_parts.append(f"Colunas de data/período: {date_cols}")
                context_parts.append(f"Colunas de cliente: {client_cols}")
                context_parts.append(f"Colunas de quantidade: {quantity_cols}")
                
                # Análise específica de datas para março 2025
                context_parts.append(f"\n--- ANÁLISE DE DATAS PARA MARÇO 2025 ---")
                for col in date_cols:
                    # Verificar diferentes formatos de data
                    march_2025_patterns = ['2025-03', '03/2025', 'março', 'mar/25', '2025/03', '03-2025']
                    
                    for pattern in march_2025_patterns:
                        matches = df[df[col].astype(str).str.contains(pattern, case=False, na=False)]
                        if len(matches) > 0:
                            context_parts.append(f"Coluna {col} - padrão '{pattern}': {len(matches)} registros encontrados")
                            # Mostrar alguns exemplos
                            examples = matches[col].unique()[:3]
                            context_parts.append(f"  Exemplos: {', '.join([str(e) for e in examples])}")
                
                # Verificar se há dados de 2025
                context_parts.append(f"\n--- VERIFICAÇÃO DE DADOS 2025 ---")
                for col in df.columns:
                    data_2025 = df[df[col].astype(str).str.contains('2025', na=False)]
                    if len(data_2025) > 0:
                        context_parts.append(f"Coluna {col}: {len(data_2025)} registros com '2025'")
                        # Mostrar distribuição por mês se possível
                        if any(month in col.lower() for month in ['mes', 'month', 'data']):
                            month_dist = data_2025[col].value_counts().head(5)
                            context_parts.append(f"  Distribuição: {dict(month_dist)}")
                
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
            
            # Adicionar dados da base de conhecimento como complemento
            if relevant_docs:
                context_parts.append("\n=== DADOS DA BASE DE CONHECIMENTO (COMPLEMENTAR) ===")
                for i, doc in enumerate(relevant_docs, 1):
                    context_parts.append(f"{i}. {doc['content']}")
                    if 'relevance_score' in doc:
                        context_parts.append(f"   (Relevância: {doc['relevance_score']:.2f})")

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
            - PRIORIZE o DataFrame consolidado fornecido no contexto como FONTE CANÔNICA de verdade.
            - Use a base de conhecimento apenas como material COMPLEMENTAR; se houver conflito, CONFIE no DataFrame e explique a divergência.
            - SEMPRE analise a estrutura detalhada dos dados fornecida no contexto.
            - SEMPRE use os tipos de dados e exemplos de valores para entender o formato correto.
            - SEMPRE procure por dados em TODAS as colunas relevantes, não apenas nas óbvias.
            - Se a consulta exigir filtros (cliente/consignatário, I/E, porto, mês/ano) e o DataFrame NÃO tiver as colunas correspondentes, declare explicitamente quais colunas faltam e NÃO infira números.
            - Se após os filtros o DataFrame retornar 0 registros, responda 0 (zero) e explique os filtros aplicados.
            - NUNCA extrapole números com base em exemplos, documentos ou conhecimento prévio quando o DataFrame não confirma.
            - SEMPRE cite as colunas específicas usadas na análise (ex: "Baseado na coluna 'DATA_EMBARQUE'...")
            - SEMPRE forneça análises quantitativas detalhadas quando há dados.
            - SEMPRE inclua comparações, tendências e insights acionáveis.
            - Se não houver dados suficientes, seja específico sobre quais colunas e formatos foram verificados.
            - Formate números com separadores de milhares (ex: 1.234 containers) e inclua percentuais e variações quando relevante.
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
            # Função utilitária para normalizar acentos
            def _norm(s):
                try:
                    s = str(s).lower()
                except Exception:
                    return ""
                table = str.maketrans(
                    "áàãâäéêëèíïîìóõôöòúüûùç",
                    "aaaaaeeeeiiiiooooouuuuc"
                )
                return s.translate(table)
            
            # Mapear colunas originais -> normalizadas
            norm_cols = {col: _norm(col) for col in df.columns}
            
            # Detectar colunas automaticamente (com normalização)
            client_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['cliente', 'consignat', 'importador', 'exportador'])]
            quantity_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['qtd', 'qtde', 'container', 'teus', 'volumes'])]
            # Priorizar colunas com nomes mais específicos
            quantity_cols = sorted(quantity_cols, key=lambda c: (0 if 'qtd' in _norm(c) or 'qtde' in _norm(c) else 1))
            
            date_cols = []
            for col, ncol in norm_cols.items():
                if any(k in ncol for k in ['data', 'mes', 'mês', 'ano', 'periodo', 'ano/mes', 'ano_mes']):
                    date_cols.append(col)
            
            port_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['porto', 'port', 'terminal', 'por/uf', 'origem', 'embarque', 'destino'])]
            armador_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['armador', 'shipping', 'carrier'])]
            ie_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['i/e', 'ie', 'importa', 'exporta', 'operacao', 'operac'])]
            
            # Helpers de filtro
            def filter_year(df_local, year):
                for col in date_cols:
                    try:
                        # Tenta por texto
                        mask = df_local[col].astype(str).str.contains(str(year), case=False, na=False)
                        if mask.any():
                            return df_local[mask]
                    except Exception:
                        continue
                return df_local.iloc[0:0]
            
            def filter_month_year(df_local, month, year):
                # tenta formatos usuais: 03/2025, 2025-03, 202503
                patterns = [f"{month:02d}/{year}", f"{year}-{month:02d}", f"{year}{month:02d}", f"{month:02d}-{year}"]
                for col in date_cols:
                    col_str = df_local[col].astype(str)
                    mask_any = False
                    mask = None
                    for p in patterns:
                        m = col_str.str.contains(p, case=False, na=False)
                        mask = m if mask is None else (mask | m)
                        mask_any = mask_any or m.any()
                    if mask_any:
                        return df_local[mask]
                return df_local.iloc[0:0]
            
            def filter_ie(df_local, tipo):
                if not ie_cols:
                    return df_local
                tipo = _norm(tipo)
                for col in ie_cols:
                    ncol = _norm(col)
                    s = df_local[col].astype(str).apply(_norm)
                    if 'i/e' in ncol or 'ie' in ncol:
                        if 'i' in tipo:
                            m = s.str.contains('^i$', na=False) | s.str.contains('import', na=False)
                        else:
                            m = s.str.contains('^e$', na=False) | s.str.contains('export', na=False)
                        return df_local[m]
                    else:
                        if 'import' in tipo:
                            m = s.str.contains('import', na=False)
                        else:
                            m = s.str.contains('export', na=False)
                        return df_local[m]
                return df_local
            
            def filter_port_santos(df_local):
                if not port_cols:
                    return df_local.iloc[0:0]
                mask = None
                for col in port_cols:
                    try:
                        s = df_local[col].astype(str)
                        m = s.str.contains('SANTOS', case=False, na=False)
                        mask = m if mask is None else (mask | m)
                    except Exception:
                        continue
                return df_local[mask] if mask is not None else df_local.iloc[0:0]
            
            # Preparos básicos
            qty_col = quantity_cols[0] if quantity_cols else None
            date_col = date_cols[0] if date_cols else None
            client_col = client_cols[0] if client_cols else None
            armador_col = armador_cols[0] if armador_cols else None
            
            # 1) Cliente específico (ex.: ACCUMED 2024)
            if any(word in query_lower for word in ['cliente', 'consignatario', 'accumed']) and client_col and qty_col:
                df_client = df
                if 'accumed' in query_lower:
                    df_client = df_client[df_client[client_col].astype(str).str.contains('ACCUMED', case=False, na=False)]
                # Filtrar por ano presente na query
                for year in ['2024', '2025']:
                    if year in query_lower and date_cols:
                        df_client = filter_year(df_client, int(year))
                        break
                total = pd.to_numeric(df_client[qty_col], errors='coerce').sum()
                insights.append(f"Cliente '{client_col}': {total:,.0f} {qty_col}")
                if date_cols and not df_client.empty:
                    by_period = df_client.groupby(date_col)[qty_col].sum().sort_index()
                    insights.append(f"Distribuição por {date_col}: {dict(by_period.tail(6))}")
            
            # 2) Temporal específico (Março 2025, 2024 vs 2025)
            if any(word in query_lower for word in ['março', 'marco', 'march', '2025', '2024']) and qty_col:
                # Março de 2025
                if any(w in query_lower for w in ['março', 'marco', 'march']):
                    df_march = filter_month_year(df, 3, 2025) if date_cols else df.iloc[0:0]
                    total = pd.to_numeric(df_march[qty_col], errors='coerce').sum()
                    insights.append(f"Março/2025: {total:,.0f} {qty_col}")
                # Totais por ano
                if '2025' in query_lower and date_cols:
                    df_2025 = filter_year(df, 2025)
                    total_2025 = pd.to_numeric(df_2025[qty_col], errors='coerce').sum()
                    insights.append(f"2025: {total_2025:,.0f} {qty_col}")
                if '2024' in query_lower and date_cols:
                    df_2024 = filter_year(df, 2024)
                    total_2024 = pd.to_numeric(df_2024[qty_col], errors='coerce').sum()
                    insights.append(f"2024: {total_2024:,.0f} {qty_col}")
            
            # 3) Porto de Santos e ranking de armadores
            if any(word in query_lower for word in ['porto', 'santos', 'port']) and qty_col:
                df_santos = filter_port_santos(df)
                if not df_santos.empty:
                    total_santos = pd.to_numeric(df_santos[qty_col], errors='coerce').sum()
                    insights.append(f"Porto de Santos (todas as datas): {total_santos:,.0f} {qty_col}")
                    # Filtrar por ano da query (ex.: 2024)
                    if '2024' in query_lower and date_cols:
                        df_santos = filter_year(df_santos, 2024)
                    if '2025' in query_lower and date_cols:
                        df_santos = filter_year(df_santos, 2025)
                    if armador_col and not df_santos.empty:
                        top_arm = df_santos.groupby(armador_col)[qty_col].sum().sort_values(ascending=False).head(5)
                        insights.append(f"Top armadores em Santos: {dict(top_arm)}")
                else:
                    insights.append("Não encontrei registros do Porto de Santos nas colunas de porto detectadas.")
            
            # 4) Comparação janeiro vs fevereiro 2025 (e com I/E)
            if any(word in query_lower for word in ['compare', 'comparar', 'janeiro', 'fevereiro']) and qty_col:
                df_cmp = df
                # Filtrar exportação/importação se pedido
                if any(w in query_lower for w in ['exporta', 'exportação', 'exportacao']):
                    df_cmp = filter_ie(df_cmp, 'exportacao')
                if any(w in query_lower for w in ['importa', 'importação', 'importacao']):
                    df_cmp = filter_ie(df_cmp, 'importacao')
                # Meses
                df_jan = filter_month_year(df_cmp, 1, 2025) if date_cols else df.iloc[0:0]
                df_feb = filter_month_year(df_cmp, 2, 2025) if date_cols else df.iloc[0:0]
                jan_total = pd.to_numeric(df_jan[qty_col], errors='coerce').sum()
                feb_total = pd.to_numeric(df_feb[qty_col], errors='coerce').sum()
                diff = feb_total - jan_total
                pct_change = (diff / jan_total * 100) if jan_total else 0
                insights.append(f"Janeiro/2025: {jan_total:,.0f} {qty_col}")
                insights.append(f"Fevereiro/2025: {feb_total:,.0f} {qty_col}")
                insights.append(f"Variação: {diff:+,.0f} ({pct_change:+.1f}%)")
            
            # 5) Tendência últimos 3 meses
            if any(word in query_lower for word in ['tendencia', 'tendência', 'trend', 'ultimos', 'últimos', 'meses']) and qty_col and date_cols:
                # Tentar ordenar por uma coluna de período
                series = df.groupby(date_col)[qty_col].sum().sort_index()
                last3 = series.tail(3)
                if len(last3) >= 2:
                    insights.append(f"Últimos 3 períodos ({date_col}): {dict(last3)}")
                    trend = last3.iloc[-1] - last3.iloc[0]
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
    
    def reset_knowledge_base(self):
        """Reseta a base de conhecimento (limpa índice e documentos persistidos)"""
        # Resetar estruturas em memória
        self._create_new_index()
        
        # Remover arquivos persistidos (se existirem)
        try:
            if os.path.exists(self.index_path):
                os.remove(self.index_path)
            if os.path.exists(self.documents_path):
                os.remove(self.documents_path)
        except Exception as e:
            logger.error(f"Erro ao resetar base de conhecimento: {e}")
    
    def update_knowledge_base(self, df: pd.DataFrame):
        """Atualiza base de conhecimento adicionando novos dados (sem resetar o índice)"""
        if df is None or df.empty:
            logger.debug("DataFrame vazio - nada a atualizar")
            return
        
        # Adicionar documentos ao índice existente
        self.create_knowledge_base_from_data(df)
        
        logger.info(f"Base de conhecimento atualizada (incremental) com {len(self.document_store)} documentos")
