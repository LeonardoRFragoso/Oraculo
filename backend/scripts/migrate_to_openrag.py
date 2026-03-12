#!/usr/bin/env python3
"""
Script de migração de dados do sistema legado (FAISS) para OpenRAG
Migra documentos existentes e arquivos processados
"""
import sys
import os
import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.openrag_integration import OpenRAGManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Gerenciador de migração de dados para OpenRAG"""
    
    def __init__(self):
        self.openrag = OpenRAGManager()
        self.root_dir = Path(__file__).parent.parent
        self.backup_dir = self.root_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def check_openrag_health(self) -> bool:
        """Verifica se OpenRAG está disponível"""
        logger.info("🔍 Verificando saúde do OpenRAG...")
        health = self.openrag.health_check()
        
        if health['overall']:
            logger.info("✅ OpenRAG está saudável e pronto")
            logger.info(f"   - Langflow: {'✅' if health['langflow'] else '❌'}")
            logger.info(f"   - OpenSearch: {'✅' if health['opensearch'] else '❌'}")
            return True
        else:
            logger.error("❌ OpenRAG não está disponível")
            logger.error("   Execute: docker-compose -f docker-compose.openrag.yml up -d")
            return False
    
    def backup_legacy_data(self):
        """Faz backup dos dados legados"""
        logger.info("💾 Fazendo backup dos dados legados...")
        
        files_to_backup = [
            'documents.pkl',
            'vector_index.faiss'
        ]
        
        backed_up = 0
        for filename in files_to_backup:
            source = self.root_dir / filename
            if source.exists():
                dest = self.backup_dir / filename
                import shutil
                shutil.copy2(source, dest)
                logger.info(f"   ✅ Backup: {filename} -> {dest}")
                backed_up += 1
        
        logger.info(f"💾 Backup concluído: {backed_up} arquivos em {self.backup_dir}")
    
    def migrate_legacy_documents(self) -> int:
        """Migra documentos do pickle legado"""
        logger.info("📦 Migrando documentos do sistema legado...")
        
        documents_path = self.root_dir / 'documents.pkl'
        if not documents_path.exists():
            logger.warning("⚠️  Arquivo documents.pkl não encontrado")
            return 0
        
        try:
            with open(documents_path, 'rb') as f:
                old_documents = pickle.load(f)
            
            logger.info(f"   Encontrados {len(old_documents)} documentos legados")
            
            # Converter formato legado para OpenRAG
            migrated = 0
            batch_size = 100
            
            for i in range(0, len(old_documents), batch_size):
                batch = old_documents[i:i+batch_size]
                
                # Preparar documentos no formato OpenRAG
                openrag_docs = []
                for doc in batch:
                    openrag_docs.append({
                        'content': doc.get('content', ''),
                        'metadata': {
                            **doc.get('metadata', {}),
                            'source': 'legacy_migration',
                            'migrated_at': datetime.now().isoformat(),
                            'original_type': doc.get('type', 'unknown')
                        }
                    })
                
                # Criar DataFrame temporário para ingestão
                df_temp = pd.DataFrame([
                    {'content': doc['content'], **doc['metadata']}
                    for doc in openrag_docs
                ])
                
                result = self.openrag.ingest_dataframe(
                    df_temp,
                    metadata={'batch': i // batch_size, 'source': 'legacy_documents'}
                )
                
                if result['success']:
                    migrated += len(batch)
                    logger.info(f"   ✅ Migrado lote {i//batch_size + 1}: {migrated}/{len(old_documents)}")
                else:
                    logger.error(f"   ❌ Erro no lote {i//batch_size + 1}: {result.get('error')}")
            
            logger.info(f"✅ Migração de documentos legados concluída: {migrated} documentos")
            return migrated
        
        except Exception as e:
            logger.error(f"❌ Erro ao migrar documentos legados: {e}")
            return 0
    
    def migrate_processed_files(self) -> int:
        """Migra arquivos da pasta dados/processed"""
        logger.info("📊 Migrando arquivos processados...")
        
        processed_dir = self.root_dir / "dados" / "processed"
        if not processed_dir.exists():
            logger.warning("⚠️  Diretório dados/processed não encontrado")
            return 0
        
        # Encontrar todos os arquivos Excel e CSV
        excel_files = list(processed_dir.glob("*.xlsx")) + list(processed_dir.glob("*.xls"))
        csv_files = list(processed_dir.glob("*.csv"))
        all_files = excel_files + csv_files
        
        logger.info(f"   Encontrados {len(all_files)} arquivos para migrar")
        
        migrated = 0
        errors = []
        
        for file_path in all_files:
            try:
                logger.info(f"   📄 Processando: {file_path.name}")
                
                # Ler arquivo
                if file_path.suffix.lower() == '.csv':
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                if df.empty:
                    logger.warning(f"   ⚠️  Arquivo vazio: {file_path.name}")
                    continue
                
                # Ingerir no OpenRAG
                result = self.openrag.ingest_dataframe(
                    df,
                    metadata={
                        'source_file': file_path.name,
                        'source_type': 'processed_file',
                        'migrated_at': datetime.now().isoformat(),
                        'records_count': len(df)
                    }
                )
                
                if result['success']:
                    migrated += 1
                    logger.info(f"   ✅ Migrado: {file_path.name} ({len(df)} registros)")
                else:
                    errors.append(f"{file_path.name}: {result.get('error')}")
                    logger.error(f"   ❌ Erro: {file_path.name} - {result.get('error')}")
            
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
                logger.error(f"   ❌ Erro ao processar {file_path.name}: {e}")
        
        logger.info(f"✅ Migração de arquivos concluída: {migrated}/{len(all_files)} arquivos")
        
        if errors:
            logger.warning(f"⚠️  {len(errors)} erros encontrados:")
            for error in errors[:5]:  # Mostrar apenas os 5 primeiros
                logger.warning(f"   - {error}")
        
        return migrated
    
    def verify_migration(self):
        """Verifica se a migração foi bem-sucedida"""
        logger.info("🔍 Verificando migração...")
        
        stats = self.openrag.get_stats()
        
        if 'error' in stats:
            logger.error(f"❌ Erro ao obter estatísticas: {stats['error']}")
            return
        
        logger.info("📊 Estatísticas do OpenRAG:")
        logger.info(f"   - Documentos indexados: {stats.get('documents', 'N/A')}")
        logger.info(f"   - Chunks criados: {stats.get('chunks', 'N/A')}")
        logger.info(f"   - Tamanho do índice: {stats.get('size', 'N/A')}")
        
        # Testar busca
        logger.info("🔍 Testando busca semântica...")
        results = self.openrag.search("containers", top_k=3)
        
        if results:
            logger.info(f"   ✅ Busca funcionando: {len(results)} resultados encontrados")
            for i, result in enumerate(results[:3], 1):
                logger.info(f"   {i}. Score: {result.get('score', 'N/A'):.3f} - {result.get('content', '')[:80]}...")
        else:
            logger.warning("   ⚠️  Nenhum resultado encontrado na busca de teste")
    
    def run_full_migration(self):
        """Executa migração completa"""
        logger.info("=" * 70)
        logger.info("🚀 INICIANDO MIGRAÇÃO PARA OPENRAG")
        logger.info("=" * 70)
        
        # 1. Verificar saúde do OpenRAG
        if not self.check_openrag_health():
            logger.error("❌ Migração abortada: OpenRAG não disponível")
            return False
        
        # 2. Fazer backup
        self.backup_legacy_data()
        
        # 3. Migrar documentos legados
        legacy_docs = self.migrate_legacy_documents()
        
        # 4. Migrar arquivos processados
        processed_files = self.migrate_processed_files()
        
        # 5. Verificar migração
        self.verify_migration()
        
        # Resumo
        logger.info("=" * 70)
        logger.info("✅ MIGRAÇÃO CONCLUÍDA")
        logger.info("=" * 70)
        logger.info(f"📦 Documentos legados migrados: {legacy_docs}")
        logger.info(f"📊 Arquivos processados migrados: {processed_files}")
        logger.info(f"💾 Backup salvo em: {self.backup_dir}")
        logger.info("")
        logger.info("🎯 Próximos passos:")
        logger.info("   1. Verifique os dados no OpenSearch Dashboards: http://localhost:5601")
        logger.info("   2. Configure workflows no Langflow: http://localhost:7860")
        logger.info("   3. Ative OpenRAG no .env: USE_OPENRAG=true")
        logger.info("   4. Reinicie o GPTRACKER")
        logger.info("=" * 70)
        
        return True


def main():
    """Função principal"""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         GPTRACKER - Migração para OpenRAG                     ║
    ║                                                               ║
    ║  Este script migrará seus dados do sistema legado (FAISS)    ║
    ║  para o OpenRAG (Langflow + OpenSearch + Docling)            ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Confirmar migração
    response = input("\n⚠️  Deseja continuar com a migração? (s/N): ")
    if response.lower() not in ['s', 'sim', 'y', 'yes']:
        print("❌ Migração cancelada pelo usuário")
        return
    
    # Executar migração
    migrator = DataMigrator()
    success = migrator.run_full_migration()
    
    if success:
        print("\n✅ Migração concluída com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Migração falhou. Verifique os logs acima.")
        sys.exit(1)


if __name__ == "__main__":
    main()
