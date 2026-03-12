"""
Processador de arquivos - Extrai texto de diversos formatos
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import PyPDF2
import docx
import json

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processa e extrai conteúdo de diferentes tipos de arquivo"""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'PDF',
        '.docx': 'Word',
        '.xlsx': 'Excel',
        '.xls': 'Excel',
        '.csv': 'CSV',
        '.txt': 'Text',
        '.json': 'JSON'
    }
    
    def __init__(self):
        self.max_text_length = 50000  # Limite de caracteres
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Processa arquivo e extrai conteúdo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dict com texto extraído e metadados
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Formato não suportado: {extension}")
        
        logger.info(f"Processando arquivo: {file_path.name} ({extension})")
        
        # Extrair conteúdo baseado no tipo
        if extension == '.pdf':
            content = self._extract_pdf(file_path)
        elif extension == '.docx':
            content = self._extract_docx(file_path)
        elif extension in ['.xlsx', '.xls']:
            content = self._extract_excel(file_path)
        elif extension == '.csv':
            content = self._extract_csv(file_path)
        elif extension == '.txt':
            content = self._extract_text(file_path)
        elif extension == '.json':
            content = self._extract_json(file_path)
        else:
            content = ""
        
        # Limitar tamanho
        if len(content) > self.max_text_length:
            content = content[:self.max_text_length] + "\n\n[Conteúdo truncado...]"
        
        return {
            'filename': file_path.name,
            'extension': extension,
            'type': self.SUPPORTED_EXTENSIONS[extension],
            'size': file_path.stat().st_size,
            'content': content,
            'char_count': len(content),
            'success': True
        }
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extrai texto de PDF"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text.append(f"--- Página {page_num} ---\n{page_text}")
            
            return "\n\n".join(text)
        except Exception as e:
            logger.error(f"Erro ao extrair PDF: {e}")
            return f"[Erro ao processar PDF: {str(e)}]"
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extrai texto de DOCX"""
        try:
            doc = docx.Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Erro ao extrair DOCX: {e}")
            return f"[Erro ao processar DOCX: {str(e)}]"
    
    def _extract_excel(self, file_path: Path) -> str:
        """Extrai dados de Excel"""
        try:
            # Ler todas as sheets
            excel_file = pd.ExcelFile(file_path)
            sheets_content = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Criar resumo da sheet
                summary = [
                    f"=== Sheet: {sheet_name} ===",
                    f"Linhas: {len(df)}, Colunas: {len(df.columns)}",
                    f"Colunas: {', '.join(df.columns.tolist())}",
                    "",
                    "Primeiras linhas:",
                    df.head(10).to_string(index=False),
                    "",
                    "Estatísticas:",
                    df.describe().to_string() if not df.empty else "Sem dados numéricos"
                ]
                
                sheets_content.append("\n".join(summary))
            
            return "\n\n".join(sheets_content)
        except Exception as e:
            logger.error(f"Erro ao extrair Excel: {e}")
            return f"[Erro ao processar Excel: {str(e)}]"
    
    def _extract_csv(self, file_path: Path) -> str:
        """Extrai dados de CSV"""
        try:
            df = pd.read_csv(file_path)
            
            summary = [
                f"=== CSV: {file_path.name} ===",
                f"Linhas: {len(df)}, Colunas: {len(df.columns)}",
                f"Colunas: {', '.join(df.columns.tolist())}",
                "",
                "Primeiras linhas:",
                df.head(10).to_string(index=False),
                "",
                "Estatísticas:",
                df.describe().to_string() if not df.empty else "Sem dados numéricos"
            ]
            
            return "\n".join(summary)
        except Exception as e:
            logger.error(f"Erro ao extrair CSV: {e}")
            return f"[Erro ao processar CSV: {str(e)}]"
    
    def _extract_text(self, file_path: Path) -> str:
        """Extrai texto de arquivo TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Tentar com outra codificação
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Erro ao extrair TXT: {e}")
            return f"[Erro ao processar TXT: {str(e)}]"
    
    def _extract_json(self, file_path: Path) -> str:
        """Extrai dados de JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao extrair JSON: {e}")
            return f"[Erro ao processar JSON: {str(e)}]"
