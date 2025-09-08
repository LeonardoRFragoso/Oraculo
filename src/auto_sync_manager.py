"""
Sistema de Sincronização Automática para GPTRACKER
Monitora alterações em planilhas e atualiza a base de conhecimento automaticamente
"""
import json
import time
import hashlib
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import logging
from .universal_cloud_integration import UniversalCloudIntegrator
from .advanced_llm import AdvancedLLMManager

class AutoSyncManager:
    def __init__(self, llm_manager: AdvancedLLMManager):
        self.llm_manager = llm_manager
        self.cloud_integrator = UniversalCloudIntegrator()
        self.sync_config_file = Path("dados/sync_config.json")
        self.sync_config_file.parent.mkdir(parents=True, exist_ok=True)
        self.monitored_sources = self.load_sync_config()
        self.is_monitoring = False
        self.monitor_thread = None
        self.logger = logging.getLogger(__name__)
        
    def load_sync_config(self) -> List:
        """Carrega configuração de sincronização"""
        if self.sync_config_file.exists():
            try:
                with open(self.sync_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Garantir que retorna lista de sources
                    if isinstance(data, dict):
                        return data.get("sources", [])
                    elif isinstance(data, list):
                        return data
                    else:
                        return []
            except:
                return []
        return []
    
    def save_sync_config(self):
        """Salva configuração de sincronização"""
        with open(self.sync_config_file, 'w', encoding='utf-8') as f:
            json.dump({
                "sources": self.monitored_sources,
                "settings": {"check_interval": 300}
            }, f, indent=2, ensure_ascii=False)
    
    def add_source_to_monitor(self, url: str, source_type: str = "url", name: str = None) -> bool:
        """Adiciona fonte para monitoramento"""
        try:
            # Gerar hash inicial dos dados
            if source_type == "url":
                df = self.cloud_integrator.load_spreadsheet_from_url(url)
                if df is None or df.empty:
                    return False
                
                data_hash = self._generate_data_hash(df)
                
                source_info = {
                    "id": hashlib.md5(url.encode()).hexdigest(),
                    "name": name or f"Planilha {len(self.monitored_sources) + 1}",
                    "url": url,
                    "type": source_type,
                    "last_hash": data_hash,
                    "last_check": datetime.now().isoformat(),
                    "last_update": datetime.now().isoformat(),
                    "record_count": len(df),
                    "enabled": True
                }
                
                # Verificar se já existe
                existing_idx = None
                for i, source in enumerate(self.monitored_sources):
                    if source.get("url") == url:
                        existing_idx = i
                        break
                
                if existing_idx is not None:
                    self.monitored_sources[existing_idx] = source_info
                else:
                    self.monitored_sources.append(source_info)
                
                self.save_sync_config()
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao adicionar fonte: {e}")
            return False
    
    def _generate_data_hash(self, df: pd.DataFrame) -> str:
        """Gera hash dos dados para detectar mudanças"""
        # Usar informações básicas do DataFrame para gerar hash
        data_string = f"{len(df)}_{df.columns.tolist()}_{df.iloc[0].to_dict() if not df.empty else ''}"
        return hashlib.md5(data_string.encode()).hexdigest()
    
    def check_for_updates(self) -> List[Dict]:
        """Verifica atualizações em todas as fontes monitoradas"""
        updates = []
        
        # Garantir que monitored_sources é uma lista de dicionários
        if not isinstance(self.monitored_sources, list):
            self.monitored_sources = []
        
        valid_sources = [s for s in self.monitored_sources if isinstance(s, dict)]
        
        for source in valid_sources:
            if not source.get("enabled", True):
                continue
                
            try:
                if source["type"] == "url":
                    df = self.cloud_integrator.load_spreadsheet_from_url(source["url"])
                    
                    if df is not None and not df.empty:
                        current_hash = self._generate_data_hash(df)
                        
                        if current_hash != source["last_hash"]:
                            # Dados alterados
                            updates.append({
                                "source": source,
                                "old_hash": source["last_hash"],
                                "new_hash": current_hash,
                                "old_count": source.get("record_count", 0),
                                "new_count": len(df),
                                "data": df
                            })
                            
                            # Atualizar informações da fonte
                            source["last_hash"] = current_hash
                            source["last_update"] = datetime.now().isoformat()
                            source["record_count"] = len(df)
                
                source["last_check"] = datetime.now().isoformat()
                
            except Exception as e:
                self.logger.error(f"Erro ao verificar fonte {source['name']}: {e}")
        
        if updates:
            self.save_sync_config()
        
        return updates
    
    def apply_updates(self, updates: List[Dict]) -> bool:
        """Aplica atualizações na base de conhecimento"""
        try:
            for update in updates:
                df = update["data"]
                source_name = update["source"]["name"]
                
                # Atualizar base de conhecimento
                self.llm_manager.update_knowledge_base(df)
                
                self.logger.info(f"Base atualizada: {source_name} - {update['new_count']} registros")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao aplicar atualizações: {e}")
            return False
    
    def start_monitoring(self, interval_minutes: int = 5):
        """Inicia monitoramento automático"""
        if self.is_monitoring:
            return False
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_minutes,),
            daemon=True
        )
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self):
        """Para monitoramento automático"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self, interval_minutes: int):
        """Loop principal de monitoramento"""
        while self.is_monitoring:
            try:
                # Garantir que monitored_sources é uma lista válida
                if not isinstance(self.monitored_sources, list):
                    self.monitored_sources = []
                
                # Filtrar apenas dicionários válidos
                self.monitored_sources = [s for s in self.monitored_sources if isinstance(s, dict)]
                
                updates = self.check_for_updates()
                
                if updates:
                    self.apply_updates(updates)
                    
                    # Log das atualizações
                    for update in updates:
                        if isinstance(update, dict) and "source" in update:
                            source = update["source"]
                            if isinstance(source, dict):
                                source_name = source.get("name", "Fonte desconhecida")
                                old_count = update.get("old_count", 0)
                                new_count = update.get("new_count", 0)
                                self.logger.info(f"📊 Atualização detectada: {source_name} ({old_count} → {new_count} registros)")
                
                # Aguardar próxima verificação
                time.sleep(interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {e}")
                # Resetar monitored_sources em caso de erro
                self.monitored_sources = []
                time.sleep(60)  # Aguardar 1 minuto em caso de erro
    
    def get_monitoring_status(self) -> Dict:
        """Retorna status do monitoramento"""
        # Garantir que monitored_sources é uma lista
        if not isinstance(self.monitored_sources, list):
            self.monitored_sources = []
        
        # Filtrar apenas dicionários válidos
        valid_sources = [s for s in self.monitored_sources if isinstance(s, dict)]
        
        return {
            "is_monitoring": self.is_monitoring,
            "sources_count": len(valid_sources),
            "enabled_sources": len([s for s in valid_sources if s.get("enabled", True)]),
            "last_checks": [
                {
                    "name": s.get("name", "Sem nome"),
                    "last_check": s.get("last_check"),
                    "last_update": s.get("last_update"),
                    "record_count": s.get("record_count", 0),
                    "enabled": s.get("enabled", True)
                }
                for s in valid_sources
            ]
        }
    
    def remove_source(self, source_id: str) -> bool:
        """Remove fonte do monitoramento"""
        if not isinstance(self.monitored_sources, list):
            self.monitored_sources = []
            
        initial_count = len(self.monitored_sources)
        self.monitored_sources = [s for s in self.monitored_sources if isinstance(s, dict) and s.get("id") != source_id]
        
        if len(self.monitored_sources) < initial_count:
            self.save_sync_config()
            return True
        return False
    
    def toggle_source(self, source_id: str) -> bool:
        """Ativa/desativa monitoramento de uma fonte"""
        if not isinstance(self.monitored_sources, list):
            self.monitored_sources = []
            
        for source in self.monitored_sources:
            if isinstance(source, dict) and source.get("id") == source_id:
                source["enabled"] = not source.get("enabled", True)
                self.save_sync_config()
                return True
        return False
