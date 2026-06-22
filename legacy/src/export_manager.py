"""
Gerenciador de exportação de respostas para PDF e Excel
"""
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import io
import re
from typing import Dict, List, Optional, Tuple

class ExportManager:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
    def detect_tabular_data(self, text: str) -> bool:
        """Detecta se o texto contém dados tabulares"""
        # Padrões que indicam dados tabulares
        patterns = [
            r'\d+\.\s+\w+.*\d+',  # Lista numerada com dados
            r'\|\s*\w+\s*\|',     # Tabelas markdown
            r':\s*\d+',           # Dados com dois pontos
            r'Ranking|Top \d+|Lista|Principais|Maiores|Menores',  # Palavras-chave
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def extract_data_from_response(self, text: str) -> Optional[pd.DataFrame]:
        """Extrai dados estruturados da resposta do LLM"""
        try:
            # Procurar por listas numeradas
            lines = text.split('\n')
            data_rows = []
            
            for line in lines:
                line = line.strip()
                # Padrão: "1. Nome - Valor" ou "1. Nome: Valor"
                match = re.match(r'(\d+)\.\s*([^-:]+)[-:]?\s*(.+)?', line)
                if match:
                    position = match.group(1)
                    name = match.group(2).strip()
                    value = match.group(3).strip() if match.group(3) else ""
                    
                    # Extrair números do valor
                    numbers = re.findall(r'[\d,]+', value)
                    numeric_value = numbers[0].replace(',', '') if numbers else value
                    
                    data_rows.append({
                        'Posição': int(position),
                        'Nome': name,
                        'Valor': numeric_value,
                        'Detalhes': value
                    })
            
            if data_rows:
                return pd.DataFrame(data_rows)
            
            return None
            
        except Exception as e:
            print(f"Erro ao extrair dados: {e}")
            return None
    
    def generate_pdf(self, title: str, content: str, data: Optional[pd.DataFrame] = None) -> bytes:
        """Gera PDF com o conteúdo da resposta"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Data e hora
        timestamp = datetime.now().strftime("%d/%m/%Y às %H:%M")
        story.append(Paragraph(f"Gerado em: {timestamp}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Se há dados estruturados, criar tabela
        if data is not None and not data.empty:
            # Preparar dados da tabela
            table_data = [data.columns.tolist()]  # Cabeçalho
            for _, row in data.iterrows():
                table_data.append(row.tolist())
            
            # Criar tabela
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Conteúdo textual
        content_lines = content.split('\n')
        for line in content_lines:
            if line.strip():
                story.append(Paragraph(line, self.styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Rodapé
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey
        )
        story.append(Paragraph("Gerado pelo GPTRACKER - Sistema de Análise Comercial", footer_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_excel(self, title: str, content: str, data: Optional[pd.DataFrame] = None) -> bytes:
        """Gera Excel com o conteúdo da resposta"""
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Formatos
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'font_color': '#1f4e79',
                'align': 'center'
            })
            
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#d9e2f3',
                'border': 1,
                'align': 'center'
            })
            
            data_format = workbook.add_format({
                'border': 1,
                'align': 'center'
            })
            
            # Criar worksheet
            worksheet = workbook.add_worksheet('Relatório')
            
            # Título
            worksheet.merge_range('A1:D1', title, title_format)
            worksheet.write('A3', f'Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}')
            
            row = 5
            
            # Se há dados estruturados
            if data is not None and not data.empty:
                # Escrever cabeçalhos
                for col, header in enumerate(data.columns):
                    worksheet.write(row, col, header, header_format)
                
                row += 1
                
                # Escrever dados
                for _, data_row in data.iterrows():
                    for col, value in enumerate(data_row):
                        worksheet.write(row, col, value, data_format)
                    row += 1
                
                row += 2
            
            # Conteúdo textual
            worksheet.write(row, 0, 'Detalhes:')
            row += 1
            
            content_lines = content.split('\n')
            for line in content_lines:
                if line.strip():
                    worksheet.write(row, 0, line.strip())
                    row += 1
            
            # Ajustar largura das colunas
            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 30)
            worksheet.set_column('C:C', 20)
            worksheet.set_column('D:D', 30)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def create_download_buttons(self, title: str, content: str) -> Tuple[Optional[bytes], Optional[bytes]]:
        """Cria arquivos para download se a resposta contém dados tabulares"""
        if not self.detect_tabular_data(content):
            return None, None
        
        # Extrair dados estruturados
        data = self.extract_data_from_response(content)
        
        # Gerar arquivos
        pdf_data = self.generate_pdf(title, content, data)
        excel_data = self.generate_excel(title, content, data)
        
        return pdf_data, excel_data
