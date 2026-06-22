"""
Sistema de ingestão de dados flexível para GPTRACKER
Suporta múltiplos formatos e fontes de dados
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging
from .security_manager import security_manager

class DataIngestionManager:
    def __init__(self, data_dir="dados", config_file="ingestion_config.json"):
        self.data_dir = Path(data_dir)
        self.config_file = config_file
        self.supported_formats = ['.xlsx', '.xls', '.csv', '.json', '.parquet']
        self.data_schemas = self._load_schemas()
        
        # Criar diretórios necessários
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "processed").mkdir(exist_ok=True)
        (self.data_dir / "raw").mkdir(exist_ok=True)
        (self.data_dir / "archive").mkdir(exist_ok=True)
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
    
    def _load_schemas(self) -> Dict:
        """Carrega esquemas de dados configurados"""
        default_schemas = {
            "logistico": {
                "required_columns": ["qtd_container", "cliente", "ano_mes"],
                "optional_columns": ["tipo_operacao", "porto", "armador", "navio"],
                "data_types": {
                    "qtd_container": "numeric",
                    "ano_mes": "date_period",
                    "cliente": "string"
                }
            },
            "comercial": {
                "required_columns": ["cliente", "receita", "periodo"],
                "optional_columns": ["vendedor", "regiao", "produto", "margem"],
                "data_types": {
                    "receita": "numeric",
                    "periodo": "date_period",
                    "cliente": "string"
                }
            },
            "budget": {
                "required_columns": ["periodo", "meta_receita", "meta_containers"],
                "optional_columns": ["departamento", "responsavel", "observacoes"],
                "data_types": {
                    "meta_receita": "numeric",
                    "meta_containers": "numeric",
                    "periodo": "date_period"
                }
            },
            "oportunidades": {
                "required_columns": ["cliente", "valor_estimado", "probabilidade", "data_fechamento"],
                "optional_columns": ["origem", "responsavel", "status", "observacoes"],
                "data_types": {
                    "valor_estimado": "numeric",
                    "probabilidade": "percentage",
                    "data_fechamento": "date"
                }
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    custom_schemas = json.load(f)
                default_schemas.update(custom_schemas)
            except Exception as e:
                self.logger.warning(f"Erro ao carregar configurações: {e}")
        
        return default_schemas
    
    def detect_data_type(self, file_path: Path) -> Optional[str]:
        """Detecta automaticamente o tipo de dados baseado no conteúdo"""
        try:
            # Carregar amostra do arquivo
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df_sample = pd.read_excel(file_path, nrows=5)
            elif file_path.suffix.lower() == '.csv':
                df_sample = pd.read_csv(file_path, nrows=5)
            else:
                return None
            
            columns = [col.upper() for col in df_sample.columns]
            
            # Verificar correspondência com esquemas
            best_match = None
            best_score = 0
            
            for schema_name, schema in self.data_schemas.items():
                required_cols = [col.upper() for col in schema["required_columns"]]
                optional_cols = [col.upper() for col in schema.get("optional_columns", [])]
                all_schema_cols = required_cols + optional_cols
                
                # Calcular score de correspondência
                matches = sum(1 for col in columns if col in all_schema_cols)
                required_matches = sum(1 for col in required_cols if col in columns)
                
                if required_matches == len(required_cols):  # Todas as colunas obrigatórias presentes
                    score = matches / len(all_schema_cols) if all_schema_cols else 0
                    if score > best_score:
                        best_score = score
                        best_match = schema_name
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de tipo: {e}")
            return None
    
    def validate_data_schema(self, df: pd.DataFrame, schema_name: str) -> Dict:
        """Valida se os dados atendem ao esquema especificado"""
        if schema_name not in self.data_schemas:
            return {"valid": False, "errors": [f"Esquema '{schema_name}' não encontrado"]}
        
        schema = self.data_schemas[schema_name]
        errors = []
        warnings = []
        
        # Verificar colunas obrigatórias
        df_columns = [col.upper() for col in df.columns]
        required_columns = [col.upper() for col in schema["required_columns"]]
        
        missing_columns = [col for col in required_columns if col not in df_columns]
        if missing_columns:
            errors.append(f"Colunas obrigatórias ausentes: {missing_columns}")
        
        # Verificar tipos de dados
        for col, expected_type in schema.get("data_types", {}).items():
            col_upper = col.upper()
            if col_upper in df_columns:
                actual_col = next(c for c in df.columns if c.upper() == col_upper)
                
                if expected_type == "numeric":
                    if not pd.api.types.is_numeric_dtype(df[actual_col]):
                        try:
                            pd.to_numeric(df[actual_col], errors='coerce')
                        except:
                            errors.append(f"Coluna '{actual_col}' deve ser numérica")
                
                elif expected_type == "date_period":
                    # Verificar se pode ser convertido para período (YYYYMM)
                    sample_values = df[actual_col].dropna().astype(str).head(5)
                    invalid_dates = []
                    for val in sample_values:
                        if not (len(val) == 6 and val.isdigit()):
                            invalid_dates.append(val)
                    
                    if invalid_dates:
                        warnings.append(f"Coluna '{actual_col}' pode ter formatos de data inválidos: {invalid_dates[:3]}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "schema_used": schema_name
        }
    
    def normalize_column_names(self, df: pd.DataFrame, schema_name: str) -> pd.DataFrame:
        """Normaliza nomes de colunas baseado no esquema"""
        if schema_name not in self.data_schemas:
            return df
        
        df_normalized = df.copy()
        schema = self.data_schemas[schema_name]
        
        # Mapeamento de colunas comuns
        column_mappings = {
            # Logístico
            "QTDE CONTAINER": "qtd_container",
            "QTDE CONTEINER": "qtd_container", 
            "QUANTIDADE C20": "qtd_c20",
            "QUANTIDADE C40": "qtd_c40",
            "CONSIGNATÁRIO": "cliente",
            "CONSIGNATARIO FINAL": "cliente",
            "NOME EXPORTADOR": "cliente",
            "DESTINATÁRIO": "cliente",
            "ANO/MÊS": "ano_mes",
            "PORTO EMBARQUE": "porto_embarque",
            "PORTO DESCARGA": "porto_descarga",
            
            # Comercial
            "RECEITA": "receita",
            "FATURAMENTO": "receita",
            "VALOR": "receita",
            "VENDEDOR": "vendedor",
            "REGIÃO": "regiao",
            
            # Budget
            "META RECEITA": "meta_receita",
            "META CONTAINERS": "meta_containers",
            "ORÇAMENTO": "meta_receita",
            
            # Oportunidades
            "VALOR ESTIMADO": "valor_estimado",
            "PROBABILIDADE": "probabilidade",
            "DATA FECHAMENTO": "data_fechamento",
            "CLIENTE POTENCIAL": "cliente"
        }
        
        # Aplicar mapeamentos
        rename_dict = {}
        for col in df_normalized.columns:
            col_upper = col.upper()
            if col_upper in column_mappings:
                rename_dict[col] = column_mappings[col_upper]
        
        if rename_dict:
            df_normalized = df_normalized.rename(columns=rename_dict)
        
        return df_normalized
    
    def process_file(self, file_path: Union[str, Path], schema_name: Optional[str] = None, 
                    archive_original: bool = True) -> Dict:
        """Processa arquivo de dados"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"success": False, "error": "Arquivo não encontrado"}
        
        if file_path.suffix.lower() not in self.supported_formats:
            return {"success": False, "error": f"Formato não suportado: {file_path.suffix}"}
        
        try:
            # Carregar dados
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() == '.json':
                df = pd.read_json(file_path)
            elif file_path.suffix.lower() == '.parquet':
                df = pd.read_parquet(file_path)
            
            # Detectar tipo se não especificado
            if not schema_name:
                schema_name = self.detect_data_type(file_path)
                if not schema_name:
                    return {"success": False, "error": "Não foi possível detectar o tipo de dados"}
            
            # Validar esquema
            validation = self.validate_data_schema(df, schema_name)
            if not validation["valid"]:
                return {
                    "success": False, 
                    "error": "Dados não atendem ao esquema",
                    "validation": validation
                }
            
            # Normalizar colunas
            df_processed = self.normalize_column_names(df, schema_name)
            
            # Aplicar transformações específicas do tipo
            df_processed = self._apply_type_specific_transforms(df_processed, schema_name)
            
            # Validar integridade dos dados
            integrity_check = security_manager.validate_data_integrity(df_processed)
            
            # Salvar arquivo processado
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            processed_filename = f"{schema_name}_{timestamp}.xlsx"
            processed_path = self.data_dir / "processed" / processed_filename
            
            df_processed.to_excel(processed_path, index=False)
            
            # Arquivar original se solicitado
            if archive_original:
                archive_path = self.data_dir / "archive" / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                file_path.rename(archive_path)
            
            # Log da operação
            security_manager.log_access("system", "PROCESS_FILE", str(file_path), True)
            
            return {
                "success": True,
                "schema_detected": schema_name,
                "processed_file": str(processed_path),
                "records_processed": len(df_processed),
                "validation": validation,
                "integrity_check": integrity_check
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao processar arquivo {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _apply_type_specific_transforms(self, df: pd.DataFrame, schema_name: str) -> pd.DataFrame:
        """Aplica transformações específicas por tipo de dados"""
        df_transformed = df.copy()
        
        if schema_name == "logistico":
            # Unificar contagem de containers
            if 'qtd_c20' in df_transformed.columns and 'qtd_c40' in df_transformed.columns:
                df_transformed['qtd_container'] = (
                    pd.to_numeric(df_transformed['qtd_c20'], errors='coerce').fillna(0) +
                    pd.to_numeric(df_transformed['qtd_c40'], errors='coerce').fillna(0)
                )
            
            # Padronizar ano_mes
            if 'ano_mes' in df_transformed.columns:
                df_transformed['ano_mes'] = pd.to_numeric(df_transformed['ano_mes'], errors='coerce')
                df_transformed['ano'] = df_transformed['ano_mes'] // 100
                df_transformed['mes'] = df_transformed['ano_mes'] % 100
        
        elif schema_name == "comercial":
            # Converter receita para numérico
            if 'receita' in df_transformed.columns:
                df_transformed['receita'] = pd.to_numeric(
                    df_transformed['receita'].astype(str).str.replace(r'[^\d.,]', '', regex=True).str.replace(',', '.'),
                    errors='coerce'
                )
        
        elif schema_name == "oportunidades":
            # Converter probabilidade para decimal
            if 'probabilidade' in df_transformed.columns:
                prob_col = df_transformed['probabilidade']
                # Se valores > 1, assumir que está em percentual
                if prob_col.max() > 1:
                    df_transformed['probabilidade'] = prob_col / 100
        
        return df_transformed
    
    def batch_process_directory(self, directory: Union[str, Path], 
                              file_pattern: str = "*", schema_name: Optional[str] = None) -> List[Dict]:
        """Processa todos os arquivos de um diretório"""
        directory = Path(directory)
        results = []
        
        if not directory.exists():
            return [{"error": "Diretório não encontrado"}]
        
        # Encontrar arquivos
        files = []
        for ext in self.supported_formats:
            files.extend(directory.glob(f"{file_pattern}{ext}"))
        
        for file_path in files:
            result = self.process_file(file_path, schema_name)
            result["file"] = str(file_path)
            results.append(result)
        
        return results
    
    def get_processing_status(self) -> Dict:
        """Retorna status do processamento de dados"""
        processed_dir = self.data_dir / "processed"
        archive_dir = self.data_dir / "archive"
        
        processed_files = list(processed_dir.glob("*.xlsx"))
        archived_files = list(archive_dir.glob("*"))
        
        return {
            "processed_files": len(processed_files),
            "archived_files": len(archived_files),
            "last_processed": max([f.stat().st_mtime for f in processed_files]) if processed_files else None,
            "supported_formats": self.supported_formats,
            "available_schemas": list(self.data_schemas.keys())
        }

# Instância global
data_ingestion = DataIngestionManager()
