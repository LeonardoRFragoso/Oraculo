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
                specific_analysis = self._analyze_specific_query(query, df)
                context_parts.append(specific_analysis)

                # Se a análise específica trouxe números concretos, priorizar uma resposta direta
                if specific_analysis and "Análise específica não disponível" not in specific_analysis and "Erro na análise específica" not in specific_analysis:
                    direct_answer = (
                        "RESPOSTA DIRETA\n"
                        f"{specific_analysis}\n\n"
                        f"Fonte: dados consolidados ({len(df):,} registros)."
                    )
                    return direct_answer
            
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
            
            # Query normalizada para matching robusto
            q_norm = _norm(query)
            
            # Trabalhar em uma cópia e garantir numérico na coluna de quantidade quando identificada
            df_work = df.copy()
            
            # Mapear colunas originais -> normalizadas
            norm_cols = {col: _norm(col) for col in df.columns}
            
            # Detectar colunas automaticamente (com normalização)
            client_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['cliente', 'consignat', 'importador', 'exportador'])]
            quantity_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['qtd', 'qtde', 'qte', 'quant', 'container', 'cont', 'teus', 'volumes'])]
            # Priorizar colunas com nomes mais específicos
            quantity_cols = sorted(quantity_cols, key=lambda c: (0 if any(k in _norm(c) for k in ['qtd', 'qtde', 'qte']) else 1))
            
            date_cols = []
            for col, ncol in norm_cols.items():
                if any(k in ncol for k in ['data', 'mes', 'mês', 'ano', 'periodo', 'ano/mes', 'ano_mes']):
                    date_cols.append(col)
            
            port_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['porto', 'port', 'terminal', 'por/uf', 'origem', 'embarque', 'destino'])]
            armador_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['armador', 'shipping', 'carrier'])]
            ie_cols = [col for col, ncol in norm_cols.items() if any(k in ncol for k in ['i/e', 'ie', 'importa', 'exporta', 'operacao', 'operac'])]
            
            # Escolher melhor coluna de período priorizando ano_mes e datas de movimento/embarque
            def _date_score(col_name: str) -> int:
                n = _norm(col_name)
                score = 0
                if 'ano_mes' in n or 'ano/mes' in n or 'ano-mes' in n or 'mes/ano' in n:
                    score += 6
                if 'data mov' in n or 'mov' in n:
                    score += 5
                if 'embarque' in n:
                    score += 4
                if 'eta' in n or 'ets' in n:
                    score += 3
                if 'pagament' in n or 'fatura' in n or 'desconto' in n or 'emissao' in n or 'emissão' in n:
                    score -= 5
                if 'data' in n:
                    score += 1
                if 'mes' in n or 'mês' in n:
                    score += 1
                return score
            date_cols = sorted(date_cols, key=_date_score, reverse=True)
            
            # Helpers de filtro
            year_cols = [c for c, n in norm_cols.items() if 'ano' in n]
            month_cols = [c for c, n in norm_cols.items() if 'mes' in n or 'mês' in n]

            def filter_year(df_local, year):
                # 1) Colunas explícitas de ano
                for col in year_cols:
                    try:
                        m = pd.to_numeric(df_local[col], errors='coerce') == int(year)
                        if m.any():
                            return df_local[m]
                    except Exception:
                        continue
                # 2) Colunas de período (texto)
                for col in date_cols:
                    try:
                        mask = df_local[col].astype(str).str.contains(str(year), case=False, na=False)
                        if mask.any():
                            return df_local[mask]
                    except Exception:
                        continue
                # 3) Fallback: usar período canônico se existir
                try:
                    if '__period' in df_local.columns:
                        m = df_local['__period'].astype(str).str.contains(str(year), na=False)
                        if m.any():
                            return df_local[m]
                except Exception:
                    pass
                return df_local.iloc[0:0]
            
            def filter_month_year(df_local, month, year):
                # 1) Colunas separadas de ano/mês
                for ycol in year_cols:
                    try:
                        ym = pd.to_numeric(df_local[ycol], errors='coerce') == int(year)
                    except Exception:
                        ym = None
                    if ym is None or not ym.any():
                        continue
                    for mcol in month_cols:
                        try:
                            mm = pd.to_numeric(df_local[mcol], errors='coerce') == int(month)
                            if mm.any():
                                return df_local[ym & mm]
                        except Exception:
                            continue
                # 2) Colunas de período em texto: 03/2025, 2025-03, 202503, 03-2025
                patterns = [f"{month:02d}/{year}", f"{year}-{month:02d}", f"{year}{month:02d}", f"{month:02d}-{year}"]
                for col in date_cols:
                    try:
                        col_str = df_local[col].astype(str)
                        mask_any = False
                        mask = None
                        for p in patterns:
                            m = col_str.str.contains(p, case=False, na=False)
                            mask = m if mask is None else (mask | m)
                            mask_any = mask_any or m.any()
                        if mask_any:
                            return df_local[mask]
                    except Exception:
                        continue
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
                            m = s.str.contains('^i$', na=False) | s.str.contains('imp', na=False) | s.str.contains('import', na=False)
                        else:
                            m = s.str.contains('^e$', na=False) | s.str.contains('exp', na=False) | s.str.contains('export', na=False)
                        return df_local[m]
                    else:
                        if 'import' in tipo or 'imp' in tipo:
                            m = s.str.contains('import', na=False) | s.str.contains('imp', na=False)
                        else:
                            m = s.str.contains('export', na=False) | s.str.contains('exp', na=False)
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
            # Funções auxiliares para identificar melhor a coluna de quantidade
            def _to_numeric_clean(series):
                try:
                    s = pd.to_numeric(series, errors='coerce')
                    if s.notna().sum() > 0:
                        return s
                except Exception:
                    pass
                try:
                    s = series.astype(str).str.replace(r'[^0-9\-]', '', regex=True)
                    return pd.to_numeric(s, errors='coerce')
                except Exception:
                    return pd.to_numeric(series, errors='coerce')

            def _name_score(n: str) -> int:
                # Maior prioridade para nomes claros de quantidade
                score = 0
                if any(k in n for k in ['qtd', 'qtde', 'qte', 'quant']):
                    score += 10
                if any(k in n for k in ['container', 'cntr', 'cont']):
                    score += 8
                if 'teus' in n:
                    score += 6
                if 'volume' in n or 'volumes' in n:
                    score += 5
                # Penalizações para colunas indevidas
                if any(k in n for k in ['data', 'pagament', 'desconto', 'fatura', 'emissao', 'emissão', 'nota', 'nfe', 'document']):
                    score -= 20
                return score

            def _pick_qty_col(df_local):
                best = (None, -10, -1.0, -1.0)  # (col, name_score, valid_ratio, total_sum)
                for c in quantity_cols:
                    try:
                        n = _norm(c)
                        ns = _name_score(n)
                        s = _to_numeric_clean(df_local[c])
                        valid_ratio = float(s.notna().mean()) if len(s) else 0.0
                        if valid_ratio < 0.05:  # precisa ter pelo menos 5% de valores numéricos
                            continue
                        total = float(s.sum(skipna=True)) if not pd.isna(s.sum()) else 0.0
                        cand = (c, ns, valid_ratio, total)
                        if (cand[1], cand[2], cand[3]) > (best[1], best[2], best[3]):
                            best = cand
                    except Exception:
                        continue
                col = best[0]
                # Determinar rótulo amigável
                unit = 'containers'
                if col:
                    n = _norm(col)
                    if 'teus' in n:
                        unit = 'TEUs'
                    elif 'volume' in n or 'volumes' in n:
                        unit = 'volumes'
                return col, unit

            qty_col, unit_label = _pick_qty_col(df_work) if quantity_cols else (None, 'containers')
            date_col = date_cols[0] if date_cols else None
            client_col = client_cols[0] if client_cols else None
            armador_col = armador_cols[0] if armador_cols else None
            
            # Converter coluna de quantidade para numérico na cópia de trabalho
            if qty_col:
                try:
                    df_work[qty_col] = _to_numeric_clean(df_work[qty_col])
                except Exception:
                    pass

            # Helper para converter Series -> dict com ints simples (evitar np.int64 na saída)
            def _pyint_dict(series, n=6):
                out = {}
                for k, v in series.tail(n).items():
                    try:
                        out[str(k)] = int(v)
                    except Exception:
                        try:
                            out[str(k)] = float(v)
                        except Exception:
                            out[str(k)] = 0
                return out

            # Construir coluna de período (YYYY-MM) priorizando ano_mes / ano+mes / melhor data mensal
            def _build_period(df_local):
                # 1) ano_mes diretamente
                for c, n in norm_cols.items():
                    if 'ano_mes' in n or 'ano/mes' in n or 'ano-mes' in n or 'mes/ano' in n:
                        return df_local[c].astype(str), c
                # 2) ano + mes separados
                ycol = next((c for c in year_cols), None)
                mcol = next((c for c in month_cols), None)
                if ycol is not None and mcol is not None:
                    try:
                        y = pd.to_numeric(df_local[ycol], errors='coerce').fillna(0).astype(int)
                        m = pd.to_numeric(df_local[mcol], errors='coerce').fillna(0).astype(int)
                        period = y.astype(str) + '-' + m.apply(lambda x: f"{int(x):02d}")
                        return period, f"{ycol}+{mcol}"
                    except Exception:
                        pass
                # 3) Melhor coluna de data convertida para mensal
                if date_col is not None:
                    try:
                        dt = pd.to_datetime(df_local[date_col], errors='coerce', dayfirst=True)
                        period = dt.dt.to_period('M').astype(str)
                        return period, date_col
                    except Exception:
                        pass
                # 4) Fallback: string vazia
                return pd.Series([''] * len(df_local)), 'periodo'

            period_series, period_label = _build_period(df_work)
            df_work['__period'] = period_series
            
            # 1) Cliente específico (ex.: ACCUMED 2024)
            if any(word in q_norm for word in ['cliente', 'consignatario', 'consignatário', 'accumed']) and client_cols and qty_col:
                df_client = df_work
                # Filtro por ACCUMED em QUALQUER coluna candidata de cliente
                if 'accumed' in q_norm:
                    mask_any = None
                    for col in client_cols:
                        try:
                            s = df_client[col].astype(str).apply(_norm)
                            m = s.str.contains('accumed', na=False)
                            mask_any = m if mask_any is None else (mask_any | m)
                        except Exception:
                            continue
                    if mask_any is not None:
                        df_client = df_client[mask_any]
                # Filtrar por ano presente na query
                year_selected = None
                for y in ['2025', '2024', '2023']:
                    if y in q_norm:
                        df_client = filter_year(df_client, int(y))
                        year_selected = y
                        break
                total = pd.to_numeric(df_client[qty_col], errors='coerce').sum()
                entity_label = 'ACCUMED' if 'accumed' in q_norm else 'Cliente'
                if year_selected:
                    insights.append(f"{entity_label} {year_selected}: {total:,.0f} {unit_label}")
                else:
                    insights.append(f"{entity_label}: {total:,.0f} {unit_label}")
                if not df_client.empty and '__period' in df_client.columns or '__period' in df_work.columns:
                    # garantir coluna de período no recorte
                    if '__period' not in df_client.columns:
                        df_client = df_client.copy()
                        df_client['__period'] = df_work.loc[df_client.index, '__period']
                    by_period = df_client.groupby('__period')[qty_col].sum().sort_index()
                    insights.append(f"Distribuição por período: {_pyint_dict(by_period, n=6)}")
            
            # 2) Temporal específico (Março 2025, 2024 vs 2025)
            if any(word in q_norm for word in ['março', 'marco', 'march', '2025', '2024']) and qty_col:
                # Aplicar filtro I/E se solicitado na pergunta
                df_temporal = df_work
                # Se a pergunta mencionar Santos/porto, restringir a Santos aqui também
                if any(w in q_norm for w in ['santos', 'porto', 'port']):
                    df_temporal = filter_port_santos(df_temporal)
                if any(w in q_norm for w in ['exporta', 'exportação', 'exportacao']):
                    df_temporal = filter_ie(df_temporal, 'exportacao')
                if any(w in q_norm for w in ['importa', 'importação', 'importacao']):
                    df_temporal = filter_ie(df_temporal, 'importacao')

                # Março de 2025
                if any(w in q_norm for w in ['março', 'marco', 'march']):
                    df_march = filter_month_year(df_temporal, 3, 2025) if date_cols else df.iloc[0:0]
                    total = pd.to_numeric(df_march[qty_col], errors='coerce').sum()
                    op_str = ' (importações)' if any(w in q_norm for w in ['importa', 'importação', 'importacao']) else (' (exportações)' if any(w in q_norm for w in ['exporta', 'exportação', 'exportacao']) else '')
                    insights.append(f"Março/2025{op_str}: {total:,.0f} {unit_label}")
                
                # Totais por ano
                if '2025' in q_norm and date_cols:
                    df_2025 = filter_year(df_temporal, 2025)
                    total_2025 = pd.to_numeric(df_2025[qty_col], errors='coerce').sum()
                    insights.append(f"2025: {total_2025:,.0f} {unit_label}")
                if '2024' in q_norm and date_cols:
                    df_2024 = filter_year(df_temporal, 2024)
                    total_2024 = pd.to_numeric(df_2024[qty_col], errors='coerce').sum()
                    insights.append(f"2024: {total_2024:,.0f} {unit_label}")
            
            # 3) Porto de Santos e ranking de armadores
            if any(word in q_norm for word in ['porto', 'santos', 'port']) and qty_col:
                df_santos = filter_port_santos(df_work)
                if not df_santos.empty:
                    total_santos = pd.to_numeric(df_santos[qty_col], errors='coerce').sum()
                    insights.append(f"Porto de Santos (todas as datas): {total_santos:,.0f} {unit_label}")
                    # Filtrar por ano da query (ex.: 2024) e reportar explicitamente o total do ano
                    if '2024' in q_norm and date_cols:
                        df_santos_y = filter_year(df_santos, 2024)
                        total_santos_y = pd.to_numeric(df_santos_y[qty_col], errors='coerce').sum()
                        insights.append(f"Santos 2024: {total_santos_y:,.0f} {unit_label}")
                        df_santos = df_santos_y
                    if '2025' in q_norm and date_cols:
                        df_santos_y = filter_year(df_santos, 2025)
                        total_santos_y = pd.to_numeric(df_santos_y[qty_col], errors='coerce').sum()
                        insights.append(f"Santos 2025: {total_santos_y:,.0f} {unit_label}")
                        df_santos = df_santos_y
                    if armador_col and not df_santos.empty:
                        top_arm = df_santos.groupby(armador_col)[qty_col].sum().fillna(0).sort_values(ascending=False).head(5)
                        # Converter para inteiros simples
                        top_arm = {str(k): int(v) for k, v in top_arm.items()}
                        insights.append(f"Top armadores em Santos: {top_arm}")
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
                insights.append(f"Janeiro/2025: {jan_total:,.0f} {unit_label}")
                insights.append(f"Fevereiro/2025: {feb_total:,.0f} {unit_label}")
                insights.append(f"Variação: {diff:+,.0f} ({pct_change:+.1f}%)")
                # Tabela em HTML (renderiza dentro do container HTML do chat)
                html_table = (
                    "<table style='width:100%; border-collapse:collapse;'>"
                    "<thead><tr>"
                    "<th style='text-align:left; border-bottom:1px solid #ddd;'>Período</th>"
                    "<th style='text-align:right; border-bottom:1px solid #ddd;'>Quantidade</th>"
                    "</tr></thead><tbody>"
                    f"<tr><td>Jan/2025</td><td style='text-align:right;'>{jan_total:,.0f} {unit_label}</td></tr>"
                    f"<tr><td>Fev/2025</td><td style='text-align:right;'>{feb_total:,.0f} {unit_label}</td></tr>"
                    f"<tr><td><b>Variação</b></td><td style='text-align:right;'><b>{diff:+,.0f} ({pct_change:+.1f}%)</b></td></tr>"
                    "</tbody></table>"
                )
                insights.append(html_table)
            
            # 5) Tendência últimos 3 meses
            if any(word in q_norm for word in ['tendencia', 'tendência', 'trend', 'ultimos', 'últimos', 'meses']) and qty_col and date_cols:
                # Tentar ordenar por uma coluna de período
                series = df_work.groupby('__period')[qty_col].sum().sort_index()
                last3 = series.tail(3)
                if len(last3) >= 2:
                    insights.append(f"Últimos 3 períodos: {_pyint_dict(last3, n=3)}")
                    trend = last3.iloc[-1] - last3.iloc[0]
                    insights.append(f"Tendência geral: {trend:+,.0f} {unit_label}")
            
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
