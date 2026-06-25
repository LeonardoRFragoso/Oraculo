"""
Router de Exportação — gera arquivos HTML, Markdown, TXT e PDF a partir do chat.
"""

import sys
import uuid
import re
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse

from ..models import ChatRequest
from ..routers.auth import get_current_user

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from catalog.registry import DataSourceRegistry
from nl2sql.router import QueryRouter, QueryType
from rag.hybrid_retriever import HybridRetriever
from core.llm_client import LLMClient

logger = logging.getLogger(__name__)
router = APIRouter()

_registry = DataSourceRegistry()
_query_router = QueryRouter()
_hybrid = HybridRetriever()
_llm = LLMClient()

EXPORT_DIR = Path(__file__).parent.parent.parent / "dados" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_FORMATS = {"html", "md", "txt", "pdf"}


@router.post("/chat/export")
async def export_chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Gera um arquivo (html, md, txt, pdf) com base na pergunta e nas fontes selecionadas.
    """
    fmt = _extract_format(request.query)
    if not fmt or fmt not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Use html, md, txt ou pdf."
        )

    connected_sources = [
        s for s in _registry.list()
        if s.status in ("connected", "profiled", "analyzed")
    ]
    selected_ids = set(request.source_ids or [])
    active_sources = connected_sources if not selected_ids else [
        s for s in connected_sources if s.id in selected_ids
    ]

    context = await _gather_context(request.query, active_sources)
    content = await _generate_content(request.query, fmt, context)
    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{fmt}"
    filepath = EXPORT_DIR / filename

    if fmt == "pdf":
        _write_pdf(content, filepath)
    else:
        filepath.write_text(content, encoding="utf-8")

    download_url = f"/api/exports/{filename}"
    return {"download_url": download_url, "filename": filename, "format": fmt}


@router.get("/exports/{filename}")
async def download_export(filename: str):
    """Serve um arquivo gerado anteriormente."""
    filepath = EXPORT_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(
        filepath,
        media_type=_media_type(filename),
        filename=filename,
    )


def _extract_format(query: str) -> Optional[str]:
    """Tenta extrair o formato desejado a partir da pergunta do usuário."""
    q = query.lower()
    patterns = [
        (r"\bhtml\b", "html"),
        (r"\bmarkdown\b|\bmd\b", "md"),
        (r"\bpdf\b", "pdf"),
        (r"\btxt\b|\btexto\b|\btexto plano\b", "txt"),
    ]
    for pattern, fmt in patterns:
        if re.search(pattern, q):
            return fmt
    return None


async def _gather_context(query: str, active_sources: List) -> str:
    """Recupera contexto relevante das fontes selecionadas."""
    if not active_sources:
        return ""
    try:
        decision = _query_router.route(query, active_sources)
        if decision.query_type in (QueryType.NL2SQL, QueryType.RAG, QueryType.HYBRID):
            suggested = decision.suggested_sources or [s.id for s in active_sources[:3]]
            struct_sources = [
                s for s in active_sources
                if s.id in suggested and s.connector_type not in ("pdf", "docx", "txt", "xml")
            ]
            doc_sources = [
                s for s in active_sources
                if s.id in suggested and s.connector_type in ("pdf", "docx", "txt", "xml")
            ]
            result = await _hybrid.retrieve(
                question=query,
                structured_sources=struct_sources or None,
                document_sources=doc_sources or None,
            )
            parts = []
            if result.sql_results:
                parts.append("SQL Results:")
                parts.append(str(result.sql_results))
            if result.doc_chunks:
                parts.append("Document Excerpts:")
                for chunk in result.doc_chunks[:4]:
                    parts.append(chunk.content)
            return "\n\n".join(parts)
    except Exception as e:
        logger.warning(f"Context gathering for export failed: {e}")
    return ""


async def _generate_content(query: str, fmt: str, context: str) -> str:
    """Usa o LLM para gerar o conteúdo no formato solicitado."""
    system = _system_prompt_for_format(fmt)
    user = f"Pergunta: {query}\n\n"
    if context:
        user += f"Contexto das fontes de dados:\n{context}\n\n"
    user += "Gere o arquivo completo no formato solicitado."

    resp = _llm.chat(
        system=system,
        user=user,
        max_tokens=2048,
        temperature=0.3,
    )
    return resp.content.strip()


def _system_prompt_for_format(fmt: str) -> str:
    if fmt == "html":
        return (
            "Você é um assistente que gera arquivos HTML. "
            "Crie um documento HTML5 completo, bem formatado, com CSS inline básico. "
            "Não inclua explicações fora do código."
        )
    if fmt == "md":
        return (
            "Você é um assistente que gera arquivos Markdown. "
            "Crie um documento Markdown bem estruturado. "
            "Não inclua explicações fora do conteúdo."
        )
    if fmt == "pdf":
        return (
            "Você é um assistente que gera conteúdo para PDF. "
            "Crie um documento bem estruturado em texto plano com seções claras. "
            "Não inclua explicações fora do conteúdo."
        )
    return (
        "Você é um assistente que gera arquivos de texto. "
        "Crie um documento de texto plano bem estruturado. "
        "Não inclua explicações fora do conteúdo."
    )


def _find_unicode_font() -> Optional[Path]:
    """Procura uma fonte TrueType com suporte a Unicode no sistema."""
    candidates = [
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _write_pdf(text: str, filepath: Path):
    """Converte texto para PDF usando fpdf2."""
    from fpdf import FPDF

    font_path = _find_unicode_font()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_margins(10, 10)
    cell_width = 190
    if font_path:
        pdf.add_font("Unicode", "", str(font_path), uni=True)
        pdf.set_font("Unicode", size=12)
        for line in text.splitlines():
            pdf.multi_cell(cell_width, 8, line)
    else:
        pdf.set_font("Helvetica", size=12)
        for line in text.splitlines():
            try:
                encoded = line.encode("latin-1")
            except UnicodeEncodeError:
                encoded = line.encode("latin-1", "replace")
            pdf.multi_cell(cell_width, 8, encoded.decode("latin-1"))

    pdf.output(str(filepath))


def _media_type(filename: str) -> str:
    if filename.endswith(".html"):
        return "text/html"
    if filename.endswith(".md"):
        return "text/markdown"
    if filename.endswith(".txt"):
        return "text/plain"
    if filename.endswith(".pdf"):
        return "application/pdf"
    return "application/octet-stream"
