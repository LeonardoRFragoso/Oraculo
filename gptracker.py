"""
GPTRACKER - Interface Simples de Chat
Versão simplificada focada apenas em chat com histórico
"""
import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Importar módulos necessários
from src.advanced_llm import AdvancedLLMManager
from src.auth import auth_manager
from src.export_manager import ExportManager
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="GPTRACKER Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração de tema
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# CSS personalizado com suporte a dark mode
def get_css_styles():
    if st.session_state.dark_mode:
        return """
        <style>
            .stApp {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            .main-header {
                text-align: center;
                padding: 1rem 0;
                background: linear-gradient(90deg, #2d4a66, #1a365d);
                color: white;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            
            .user-message {
                background-color: #0066cc;
                color: white;
                padding: 10px 15px;
                border-radius: 15px 15px 5px 15px;
                margin: 10px 0;
                margin-left: 20%;
                text-align: right;
            }
            
            .assistant-message {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 10px 15px;
                border-radius: 15px 15px 15px 5px;
                margin: 10px 0;
                margin-right: 20%;
                border: 1px solid #404040;
            }
            
            .sidebar .sidebar-content {
                background-color: #2d2d2d;
            }
            
            .delete-btn {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 12px;
                cursor: pointer;
                margin-left: 5px;
            }
            
            .delete-btn:hover {
                background-color: #c82333;
            }
        </style>
        """
    else:
        return """
        <style>
            .main-header {
                text-align: center;
                padding: 1rem 0;
                background: linear-gradient(90deg, #1f4e79, #2d5aa0);
                color: white;
                border-radius: 10px;
                margin-bottom: 2rem;
            }
            
            .user-message {
                background-color: #007bff;
                color: white;
                padding: 10px 15px;
                border-radius: 15px 15px 5px 15px;
                margin: 10px 0;
                margin-left: 20%;
                text-align: right;
            }
            
            .assistant-message {
                background-color: #f1f1f1;
                color: #333;
                padding: 10px 15px;
                border-radius: 15px 15px 15px 5px;
                margin: 10px 0;
                margin-right: 20%;
            }
            
            .delete-btn {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 12px;
                cursor: pointer;
                margin-left: 5px;
            }
            
            .delete-btn:hover {
                background-color: #c82333;
            }
        </style>
        """

st.markdown(get_css_styles(), unsafe_allow_html=True)

class ChatHistory:
    def __init__(self):
        self.history_dir = Path("dados/chat_history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def save_conversation(self, conversation_id, messages):
        """Salva conversa no histórico"""
        file_path = self.history_dir / f"{conversation_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'id': conversation_id,
                'created_at': datetime.now().isoformat(),
                'messages': messages
            }, f, indent=2, ensure_ascii=False)
    
    def load_conversation(self, conversation_id):
        """Carrega conversa do histórico"""
        file_path = self.history_dir / f"{conversation_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def delete_conversation(self, conversation_id):
        """Deleta conversa do histórico"""
        file_path = self.history_dir / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def list_conversations(self):
        """Lista todas as conversas"""
        conversations = []
        for file_path in self.history_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Pegar primeiro user message como título
                    title = "Nova Conversa"
                    for msg in data.get('messages', []):
                        if msg.get('role') == 'user':
                            title = msg.get('content', '')[:50] + "..."
                            break
                    
                    conversations.append({
                        'id': data['id'],
                        'title': title,
                        'created_at': data['created_at']
                    })
            except:
                continue
        
        # Ordenar por data (mais recente primeiro)
        conversations.sort(key=lambda x: x['created_at'], reverse=True)
        return conversations

def initialize_session():
    """Inicializa variáveis de sessão"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if 'llm_manager' not in st.session_state:
        st.session_state.llm_manager = AdvancedLLMManager()
    
    if 'export_manager' not in st.session_state:
        st.session_state.export_manager = ExportManager()

def render_sidebar():
    """Renderiza barra lateral com histórico"""
    with st.sidebar:
        # Controles de tema e nova conversa
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("➕ Nova Conversa", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.rerun()
        
        with col2:
            # Toggle dark mode
            if st.button("🌓", help="Alternar tema", use_container_width=True):
                st.session_state.dark_mode = not st.session_state.dark_mode
                st.rerun()
        
        st.markdown("### 💬 Histórico de Conversas")
        st.markdown("---")
        
        # Seção de upload de dados
        st.markdown("### 📊 Alimentar Dados")
        
        # Auto-sync automático (sem controles manuais)
        if 'auto_sync_manager' not in st.session_state:
            from src.auto_sync_manager import AutoSyncManager
            st.session_state.auto_sync_manager = AutoSyncManager(st.session_state.llm_manager)
            # Iniciar automaticamente
            st.session_state.auto_sync_manager.start_monitoring()
        
        sync_status = st.session_state.auto_sync_manager.get_monitoring_status()
        
        # Mostrar apenas status (sem controles)
        if sync_status["enabled_sources"] > 0:
            st.info(f"🔄 Auto-sync ativo: {sync_status['enabled_sources']} planilhas monitoradas")
        
        # Upload múltiplo de arquivos
        st.markdown("**Upload de Planilhas:**")
        uploaded_files = st.file_uploader(
            "Escolha arquivos Excel ou CSV",
            type=['xlsx', 'xls', 'csv'],
            accept_multiple_files=True,
            help="Formatos suportados: .xlsx, .xls, .csv - Selecione múltiplos arquivos"
        )
        
        if uploaded_files:
            if st.button("📊 Processar Todos os Arquivos", use_container_width=True):
                total_files = len(uploaded_files)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                processed_count = 0
                total_records = 0
                errors = []
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        # Atualizar progresso
                        progress = (i + 1) / total_files
                        progress_bar.progress(progress)
                        status_text.text(f"Processando {uploaded_file.name} ({i+1}/{total_files})")
                        
                        # Ler arquivo
                        if uploaded_file.name.endswith('.csv'):
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)
                        
                        if not df.empty:
                            # Salvar arquivo processado
                            dados_dir = Path("dados/processed")
                            dados_dir.mkdir(parents=True, exist_ok=True)
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{uploaded_file.name.split('.')[0]}_{timestamp}.xlsx"
                            filepath = dados_dir / filename
                            
                            df.to_excel(filepath, index=False)
                            
                            # Atualizar base de conhecimento
                            if hasattr(st.session_state, 'llm_manager'):
                                st.session_state.llm_manager.update_knowledge_base(df)
                            
                            processed_count += 1
                            total_records += len(df)
                        else:
                            errors.append(f"{uploaded_file.name}: Arquivo vazio")
                            
                    except Exception as e:
                        error_msg = f"{uploaded_file.name}: {str(e)}"
                        if "No sheet named" in str(e):
                            error_msg = f"{uploaded_file.name}: Planilha corrompida ou inválida"
                        errors.append(error_msg)
                
                # Finalizar progresso
                progress_bar.progress(1.0)
                status_text.text("Processamento concluído!")
                
                # Mostrar resultados
                if processed_count > 0:
                    st.success(f"✅ {processed_count} arquivo(s) processado(s) com sucesso! Total: {total_records:,} registros.")
                
                if errors:
                    st.error("❌ Erros encontrados:")
                    for error in errors:
                        st.write(f"• {error}")
                
                # Limpar elementos de progresso após 3 segundos
                import time
                time.sleep(2)
                progress_bar.empty()
                status_text.empty()
        
        # Input múltiplo para links de nuvem
        st.markdown("**Links de Nuvem:**")
        
        # Área de texto para múltiplos links
        cloud_urls_text = st.text_area(
            "URLs das Planilhas (uma por linha)",
            placeholder="Cole os links do Google Sheets, OneDrive, etc.\nUm link por linha:\nhttps://docs.google.com/spreadsheets/...\nhttps://onedrive.live.com/...",
            help="Suporta Google Sheets, OneDrive, Dropbox - Cole múltiplos links, um por linha",
            height=100
        )
        
        if cloud_urls_text and st.button("🌐 Carregar Todos os Links", use_container_width=True):
            # Processar múltiplos URLs
            cloud_urls = [url.strip() for url in cloud_urls_text.split('\n') if url.strip()]
            
            if cloud_urls:
                total_urls = len(cloud_urls)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                processed_count = 0
                total_records = 0
                errors = []
                
                from src.universal_cloud_integration import UniversalCloudIntegrator
                cloud_integration = UniversalCloudIntegrator()
                
                for i, cloud_url in enumerate(cloud_urls):
                    try:
                        # Atualizar progresso
                        progress = (i + 1) / total_urls
                        progress_bar.progress(progress)
                        url_name = cloud_url.split('/')[-1][:30] + "..." if len(cloud_url) > 30 else cloud_url
                        status_text.text(f"Carregando {url_name} ({i+1}/{total_urls})")
                        
                        df = cloud_integration.load_spreadsheet_from_url(cloud_url)
                        
                        if df is not None and not df.empty:
                            # Salvar dados
                            dados_dir = Path("dados/processed")
                            dados_dir.mkdir(parents=True, exist_ok=True)
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"cloud_data_{i+1}_{timestamp}.xlsx"
                            filepath = dados_dir / filename
                            
                            df.to_excel(filepath, index=False)
                            
                            # Atualizar base de conhecimento
                            if hasattr(st.session_state, 'llm_manager'):
                                st.session_state.llm_manager.update_knowledge_base(df)
                            
                            # Adicionar automaticamente ao monitoramento
                            st.session_state.auto_sync_manager.add_source_to_monitor(
                                cloud_url, 
                                "url", 
                                f"Planilha {cloud_url.split('/')[-1][:20]}..."
                            )
                            
                            processed_count += 1
                            total_records += len(df)
                        else:
                            errors.append(f"Link {i+1}: Não foi possível carregar dados")
                            
                    except Exception as e:
                        errors.append(f"Link {i+1}: {str(e)}")
                
                # Finalizar progresso
                progress_bar.progress(1.0)
                status_text.text("Carregamento concluído!")
                
                # Mostrar resultados
                if processed_count > 0:
                    st.success(f"✅ {processed_count} planilha(s) carregada(s) e monitoramento ativado! Total: {total_records:,} registros.")
                    st.rerun()
                
                if errors:
                    st.error("❌ Erros encontrados:")
                    for error in errors:
                        st.write(f"• {error}")
                
                # Limpar elementos de progresso
                import time
                time.sleep(2)
                progress_bar.empty()
                status_text.empty()
            else:
                st.warning("Por favor, insira pelo menos um link válido.")
        
        st.markdown("---")
        
        # Listar conversas anteriores
        chat_history = ChatHistory()
        conversations = chat_history.list_conversations()
        
        for conv in conversations[:20]:  # Mostrar apenas as 20 mais recentes
            col1, col2 = st.columns([4, 1])
            
            with col1:
                if st.button(
                    conv['title'], 
                    key=f"conv_{conv['id']}",
                    use_container_width=True
                ):
                    # Carregar conversa
                    loaded_conv = chat_history.load_conversation(conv['id'])
                    if loaded_conv:
                        st.session_state.messages = loaded_conv['messages']
                        st.session_state.conversation_id = conv['id']
                        st.rerun()
            
            with col2:
                if st.button(
                    "🗑️", 
                    key=f"del_{conv['id']}",
                    help="Excluir conversa",
                    use_container_width=True
                ):
                    # Confirmar exclusão
                    if f"confirm_delete_{conv['id']}" not in st.session_state:
                        st.session_state[f"confirm_delete_{conv['id']}"] = True
                        st.rerun()
                    else:
                        # Excluir conversa
                        chat_history.delete_conversation(conv['id'])
                        # Limpar confirmação
                        del st.session_state[f"confirm_delete_{conv['id']}"]
                        st.success("Conversa excluída!")
                        st.rerun()
            
            # Mostrar confirmação se necessário
            if f"confirm_delete_{conv['id']}" in st.session_state:
                st.warning(f"Excluir '{conv['title'][:30]}...'?")
                col_confirm, col_cancel = st.columns(2)
                with col_confirm:
                    if st.button("✅ Sim", key=f"yes_{conv['id']}", use_container_width=True):
                        chat_history.delete_conversation(conv['id'])
                        del st.session_state[f"confirm_delete_{conv['id']}"]
                        st.success("Conversa excluída!")
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Não", key=f"no_{conv['id']}", use_container_width=True):
                        del st.session_state[f"confirm_delete_{conv['id']}"]
                        st.rerun()

def render_chat():
    """Renderiza interface de chat"""
    st.markdown('<div class="main-header"><h1>🤖 GPTRACKER Chat</h1></div>', unsafe_allow_html=True)
    
    # Container para mensagens
    chat_container = st.container()
    
    with chat_container:
        # Exibir mensagens
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
                
                # Verificar se a resposta contém dados tabulares e oferecer downloads
                if st.session_state.export_manager.detect_tabular_data(message["content"]):
                    col1, col2, col3 = st.columns([1, 1, 4])
                    
                    with col1:
                        # Gerar título baseado na pergunta do usuário
                        user_question = ""
                        if i > 0 and st.session_state.messages[i-1]["role"] == "user":
                            user_question = st.session_state.messages[i-1]["content"][:50] + "..."
                        
                        title = user_question or f"Relatório {datetime.now().strftime('%d/%m/%Y')}"
                        
                        # Botão PDF
                        if st.button(f"📄 PDF", key=f"pdf_{i}", help="Baixar como PDF"):
                            try:
                                pdf_data = st.session_state.export_manager.generate_pdf(
                                    title, 
                                    message["content"],
                                    st.session_state.export_manager.extract_data_from_response(message["content"])
                                )
                                st.download_button(
                                    label="📄 Baixar PDF",
                                    data=pdf_data,
                                    file_name=f"gptracker_relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                    key=f"download_pdf_{i}"
                                )
                            except Exception as e:
                                st.error(f"Erro ao gerar PDF: {str(e)}")
                    
                    with col2:
                        # Botão Excel
                        if st.button(f"📊 Excel", key=f"excel_{i}", help="Baixar como Excel"):
                            try:
                                excel_data = st.session_state.export_manager.generate_excel(
                                    title,
                                    message["content"],
                                    st.session_state.export_manager.extract_data_from_response(message["content"])
                                )
                                st.download_button(
                                    label="📊 Baixar Excel",
                                    data=excel_data,
                                    file_name=f"gptracker_relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"download_excel_{i}"
                                )
                            except Exception as e:
                                st.error(f"Erro ao gerar Excel: {str(e)}")
    
    # Input para nova mensagem
    st.markdown("---")
    
    # Usar form para capturar Enter
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        
        with col1:
            user_input = st.text_input(
                "Digite sua pergunta...",
                placeholder="Como posso ajudar você hoje?",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.form_submit_button("Enviar", use_container_width=True)
    
    # Processar mensagem
    if submit and user_input:
        # Adicionar mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Gerar resposta
        with st.spinner("Pensando..."):
            try:
                # Preparar contexto
                context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-5:]])
                
                # Verificar se OpenAI API key está configurada
                openai_key = os.getenv('OPENAI_API_KEY')
                if not openai_key or openai_key == 'sk-sua-chave-openai-aqui':
                    response = """
🔑 **Chave OpenAI não configurada!**

Para usar o chat, você precisa:

1. **Obter uma chave da OpenAI:**
   - Acesse: https://platform.openai.com/api-keys
   - Crie uma conta e gere sua API key

2. **Configurar no arquivo .env:**
   - Abra o arquivo `.env` na raiz do projeto
   - Substitua `sk-sua-chave-openai-aqui` pela sua chave real
   - Exemplo: `OPENAI_API_KEY=sk-proj-abc123...`

3. **Reinicie o aplicativo**

Sem a chave da OpenAI, não posso processar suas perguntas.
                    """
                else:
                    # Carregar dados processados mais recentes se disponíveis
                    current_df = None
                    dados_dir = Path("dados/processed")
                    
                    if dados_dir.exists():
                        # Buscar arquivo mais recente
                        excel_files = list(dados_dir.glob("*.xlsx"))
                        if excel_files:
                            latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
                            try:
                                current_df = pd.read_excel(latest_file)
                                print(f"Dados carregados: {len(current_df)} registros de {latest_file.name}")
                            except Exception as e:
                                print(f"Erro ao carregar dados: {e}")
                    
                    # Usar o método aprimorado de geração de resposta
                    response = st.session_state.llm_manager.generate_response(
                        query=user_input,
                        context="",
                        conversation_history=st.session_state.messages[-5:] if st.session_state.messages else None,
                        df=current_df
                    )
                
                # Adicionar resposta do assistente
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Salvar conversa
                chat_history = ChatHistory()
                chat_history.save_conversation(st.session_state.conversation_id, st.session_state.messages)
                
            except Exception as e:
                error_msg = str(e)
                if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                    response = """
🔑 **Erro de Autenticação OpenAI**

Sua chave da OpenAI pode estar inválida ou expirada.

**Soluções:**
1. Verifique se a chave no arquivo `.env` está correta
2. Acesse https://platform.openai.com/api-keys para verificar sua chave
3. Certifique-se de que sua conta OpenAI tem créditos disponíveis

**Erro técnico:** """ + error_msg
                else:
                    response = f"""
❌ **Erro no Sistema**

Ocorreu um problema técnico:
```
{error_msg}
```

**Tente:**
1. Fazer uma pergunta mais simples
2. Reiniciar o aplicativo
3. Verificar sua conexão com a internet
                    """
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })
        
        st.rerun()

def main():
    """Função principal"""
    # Verificar autenticação
    if not auth_manager.require_auth():
        return
    
    # Inicializar sessão
    initialize_session()
    
    # Renderizar interface
    render_sidebar()
    render_chat()

if __name__ == "__main__":
    main()
