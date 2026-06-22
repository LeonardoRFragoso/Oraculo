"""
Módulo de segurança e governança de dados para GPTRACKER
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from cryptography.fernet import Fernet
import logging

class SecurityManager:
    def __init__(self, log_file="security_audit.log"):
        self.log_file = log_file
        self.setup_logging()
        self.encryption_key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
    def setup_logging(self):
        """Configura sistema de auditoria"""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def _get_or_create_key(self) -> bytes:
        """Obtém ou cria chave de criptografia"""
        key_file = "encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Criptografa dados sensíveis"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Erro na criptografia: {str(e)}")
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Descriptografa dados sensíveis"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Erro na descriptografia: {str(e)}")
            return encrypted_data
    
    def log_access(self, username: str, action: str, resource: str, success: bool = True):
        """Registra acesso a recursos"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'username': username,
            'action': action,
            'resource': resource,
            'success': success,
            'ip_address': self._get_client_ip()
        }
        
        if success:
            self.logger.info(f"ACCESS: {username} - {action} - {resource}")
        else:
            self.logger.warning(f"ACCESS_DENIED: {username} - {action} - {resource}")
    
    def _get_client_ip(self) -> str:
        """Obtém IP do cliente (placeholder)"""
        return "127.0.0.1"  # Em produção, obter do request
    
    def validate_data_integrity(self, df: pd.DataFrame) -> Dict:
        """Valida integridade dos dados"""
        validation_results = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'statistics': {}
        }
        
        if df.empty:
            validation_results['valid'] = False
            validation_results['issues'].append("Dataset vazio")
            return validation_results
        
        # Verificar colunas obrigatórias
        required_columns = ['qtd_container', 'cliente', 'ano_mes']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            validation_results['valid'] = False
            validation_results['issues'].append(f"Colunas obrigatórias ausentes: {missing_columns}")
        
        # Verificar valores nulos em campos críticos
        for col in required_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    validation_results['warnings'].append(f"Coluna {col} tem {null_count} valores nulos")
        
        # Verificar valores negativos em quantidade
        if 'qtd_container' in df.columns:
            negative_count = (df['qtd_container'] < 0).sum()
            if negative_count > 0:
                validation_results['issues'].append(f"{negative_count} registros com quantidade negativa")
        
        # Estatísticas gerais
        validation_results['statistics'] = {
            'total_records': len(df),
            'date_range': {
                'min': df['ano_mes'].min() if 'ano_mes' in df.columns else None,
                'max': df['ano_mes'].max() if 'ano_mes' in df.columns else None
            },
            'unique_clients': df['cliente'].nunique() if 'cliente' in df.columns else 0
        }
        
        return validation_results
    
    def anonymize_client_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Anonimiza dados de clientes para relatórios"""
        if df.empty or 'cliente' not in df.columns:
            return df
        
        df_anon = df.copy()
        
        # Criar mapeamento de clientes para IDs anônimos
        unique_clients = df['cliente'].unique()
        client_mapping = {
            client: f"CLIENTE_{i+1:03d}" 
            for i, client in enumerate(unique_clients)
        }
        
        df_anon['cliente'] = df_anon['cliente'].map(client_mapping)
        
        self.logger.info(f"Dados anonimizados: {len(unique_clients)} clientes")
        
        return df_anon
    
    def create_data_backup(self, df: pd.DataFrame, backup_type: str = "daily"):
        """Cria backup dos dados"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{backup_type}_{timestamp}.xlsx"
            backup_path = os.path.join("backups", backup_filename)
            
            os.makedirs("backups", exist_ok=True)
            
            df.to_excel(backup_path, index=False)
            
            self.logger.info(f"Backup criado: {backup_filename}")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {str(e)}")
            return None
    
    def get_access_logs(self, username: str = None, days: int = 7) -> List[Dict]:
        """Obtém logs de acesso"""
        try:
            logs = []
            
            if not os.path.exists(self.log_file):
                return logs
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    if 'ACCESS' in line:
                        # Parse básico do log (implementar parser mais robusto)
                        parts = line.strip().split(' - ')
                        if len(parts) >= 4:
                            log_entry = {
                                'timestamp': parts[0],
                                'level': parts[1],
                                'message': parts[2]
                            }
                            
                            if username is None or username in line:
                                logs.append(log_entry)
            
            return logs[-100:]  # Últimos 100 registros
            
        except Exception as e:
            self.logger.error(f"Erro ao ler logs: {str(e)}")
            return []
    
    def check_data_quality(self, df: pd.DataFrame) -> Dict:
        """Verifica qualidade dos dados"""
        quality_report = {
            'score': 100,
            'issues': [],
            'recommendations': []
        }
        
        if df.empty:
            quality_report['score'] = 0
            quality_report['issues'].append("Dataset vazio")
            return quality_report
        
        # Verificar duplicatas
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            quality_report['score'] -= 10
            quality_report['issues'].append(f"{duplicates} registros duplicados encontrados")
            quality_report['recommendations'].append("Remover registros duplicados")
        
        # Verificar consistência de datas
        if 'ano_mes' in df.columns:
            invalid_dates = df[df['ano_mes'].astype(str).str.len() != 6].shape[0]
            if invalid_dates > 0:
                quality_report['score'] -= 15
                quality_report['issues'].append(f"{invalid_dates} datas em formato inválido")
        
        # Verificar outliers em quantidade
        if 'qtd_container' in df.columns:
            Q1 = df['qtd_container'].quantile(0.25)
            Q3 = df['qtd_container'].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[
                (df['qtd_container'] < Q1 - 1.5 * IQR) | 
                (df['qtd_container'] > Q3 + 1.5 * IQR)
            ].shape[0]
            
            if outliers > len(df) * 0.05:  # Mais de 5% outliers
                quality_report['score'] -= 5
                quality_report['issues'].append(f"{outliers} possíveis outliers em quantidade")
        
        # Verificar completude dos dados
        completeness = (df.notna().sum() / len(df) * 100).mean()
        if completeness < 90:
            quality_report['score'] -= 20
            quality_report['issues'].append(f"Completude dos dados: {completeness:.1f}%")
            quality_report['recommendations'].append("Melhorar coleta de dados")
        
        return quality_report
    
    def generate_security_report(self, df: pd.DataFrame, username: str) -> Dict:
        """Gera relatório de segurança"""
        validation = self.validate_data_integrity(df)
        quality = self.check_data_quality(df)
        access_logs = self.get_access_logs(username)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'generated_by': username,
            'data_integrity': validation,
            'data_quality': quality,
            'access_summary': {
                'total_accesses': len(access_logs),
                'recent_accesses': len([log for log in access_logs if 'ACCESS:' in log.get('message', '')])
            },
            'security_score': min(100, (quality['score'] + (100 if validation['valid'] else 50)) / 2),
            'recommendations': quality.get('recommendations', [])
        }
        
        self.log_access(username, "GENERATE_SECURITY_REPORT", "security_report")
        
        return report

# Instância global
security_manager = SecurityManager()
