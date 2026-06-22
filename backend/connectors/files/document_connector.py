"""
DocumentConnector handles unstructured formats: PDF, DOCX, TXT, XML.
These produce raw_text for the RAG pipeline rather than DataFrames.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import (
    ConnectorResult, ConnectorType,
    DataConnector, DatasetInfo,
)

logger = logging.getLogger(__name__)

_TYPE_MAP = {
    ".pdf": ConnectorType.PDF,
    ".docx": ConnectorType.DOCX,
    ".txt": ConnectorType.TXT,
    ".xml": ConnectorType.XML,
}


class DocumentConnector(DataConnector):
    """
    Unified connector for document formats (PDF, DOCX, TXT, XML).

    config keys:
        path (str): file path
    """

    @property
    def connector_type(self) -> ConnectorType:
        ext = Path(self.config["path"]).suffix.lower()
        return _TYPE_MAP.get(ext, ConnectorType.TXT)

    def connect(self) -> bool:
        path = Path(self.config["path"])
        if not path.exists():
            logger.error(f"Document not found: {path}")
            return False
        self._connected = True
        return True

    def discover(self) -> List[DatasetInfo]:
        path = Path(self.config["path"])
        return [DatasetInfo(
            name=path.stem,
            connector_type=self.connector_type,
            row_count=0,
            column_count=0,
            size_bytes=path.stat().st_size,
            source_path=str(path),
            extra={"document_type": self.connector_type.value},
        )]

    def extract(self, dataset_name: Optional[str] = None) -> ConnectorResult:
        path = Path(self.config["path"])
        ext = path.suffix.lower()
        try:
            if ext == ".pdf":
                text = self._extract_pdf(path)
            elif ext == ".docx":
                text = self._extract_docx(path)
            elif ext == ".xml":
                text = self._extract_xml(path)
            else:
                text = self._extract_text(path)

            datasets = self.discover()
            datasets[0].extra["char_count"] = len(text)

            return ConnectorResult(
                success=True,
                connector_type=self.connector_type,
                datasets=datasets,
                raw_text=text,
                metadata={"char_count": len(text)},
            )
        except Exception as e:
            logger.error(f"Document extract error [{ext}]: {e}")
            return ConnectorResult(success=False, connector_type=self.connector_type, error=str(e))

    def _extract_pdf(self, path: Path) -> str:
        try:
            import PyPDF2
            pages = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append(f"--- Página {i} ---\n{text}")
            return "\n\n".join(pages)
        except ImportError:
            raise RuntimeError("PyPDF2 not installed. Run: pip install PyPDF2")

    def _extract_docx(self, path: Path) -> str:
        try:
            import docx
            doc = docx.Document(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            raise RuntimeError("python-docx not installed. Run: pip install python-docx")

    def _extract_xml(self, path: Path) -> str:
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(path)
            root = tree.getroot()
            texts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    texts.append(f"{elem.tag}: {elem.text.strip()}")
                for attr_key, attr_val in elem.attrib.items():
                    texts.append(f"{elem.tag}[@{attr_key}]: {attr_val}")
            return "\n".join(texts)
        except Exception as e:
            logger.error(f"XML parse error: {e}")
            raise

    def _extract_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")
