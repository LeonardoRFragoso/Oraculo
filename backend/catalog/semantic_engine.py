"""
Fase 0 — Universal Semantic Engine

Automatically classifies any dataset into a business domain
(Financial, HR, CRM, Logistics, etc.) using:
  1. Pattern matching on table/column names  (fast, no API cost)
  2. LLM-based classification fallback       (for ambiguous cases)

This enables automatic KPI generation and proactive AI Data Analyst
features without any manual user configuration.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from connectors.base import DataDomain, DatasetInfo  # noqa: E402 — backend root on sys.path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain signal dictionaries
# Each key is a DataDomain; values are keyword lists matched against
# table names, column names and sample values (lowercased).
# ---------------------------------------------------------------------------
_DOMAIN_SIGNALS: Dict[DataDomain, List[str]] = {
    DataDomain.FINANCIAL: [
        "invoice", "payment", "revenue", "receita", "fatura", "pagamento",
        "billing", "cobranca", "cobrança", "financeiro", "finance",
        "transaction", "transacao", "transação", "ledger", "account",
        "conta", "despesa", "expense", "profit", "lucro", "budget",
        "orcamento", "orçamento", "tax", "imposto", "debit", "credit",
        "balance", "saldo", "margin", "margem", "cost", "custo",
        "preco", "preço", "price", "valor", "amount", "total",
        "recebiveis", "recebíveis", "payable", "receivable",
    ],
    DataDomain.HR: [
        "employee", "funcionario", "funcionário", "colaborador",
        "staff", "worker", "salario", "salário", "salary", "wage",
        "folha", "payroll", "contratacao", "contratação", "hiring",
        "beneficio", "benefício", "benefit", "ferias", "férias",
        "vacation", "holerite", "cargo", "position", "job", "role",
        "department", "departamento", "admissao", "demissao",
        "admissão", "demissão", "rh", "hr", "headcount", "ponto",
        "attendance", "treinamento", "training",
    ],
    DataDomain.CRM: [
        "customer", "cliente", "prospect", "lead", "contact",
        "contato", "account", "opportunity", "oportunidade",
        "pipeline", "deal", "negocio", "negócio", "crm",
        "sales", "venda", "vendas", "seller", "vendedor",
        "churn", "retention", "retencao", "retenção", "nps",
        "satisfaction", "satisfacao", "satisfação", "loyalty",
        "fidelidade", "upsell", "cross_sell",
    ],
    DataDomain.LOGISTICS: [
        "shipment", "embarque", "container", "freight", "frete",
        "delivery", "entrega", "transport", "transporte", "carrier",
        "transportadora", "warehouse", "armazem", "armazém",
        "estoque", "stock", "inventory", "rota", "route",
        "tracking", "rastreio", "porto", "port", "navio", "vessel",
        "armador", "carga", "cargo", "logistica", "logística",
        "expedition", "expedicao", "expedição",
    ],
    DataDomain.ECOMMERCE: [
        "order", "pedido", "cart", "carrinho", "checkout",
        "product", "produto", "sku", "catalog", "catalogo",
        "catálogo", "category", "categoria", "seller", "marketplace",
        "store", "loja", "item", "basket", "session", "abandonment",
        "conversion", "revenue", "gmv", "shipping", "refund",
        "devolucao", "devolução", "rating", "review", "avaliacao",
    ],
    DataDomain.MARKETING: [
        "campaign", "campanha", "lead", "click", "impression",
        "impressao", "impressão", "ctr", "cpc", "cpm", "roi",
        "roas", "ad", "anuncio", "anúncio", "channel", "canal",
        "email", "sms", "social", "media", "midia", "mídia",
        "audience", "audiencia", "audiência", "segment", "segmento",
        "utm", "conversion", "funnel", "funil", "analytics",
    ],
    DataDomain.SUPPORT: [
        "ticket", "chamado", "incident", "incidente", "case",
        "caso", "support", "suporte", "helpdesk", "sla",
        "resolution", "resolucao", "resolução", "agent", "atendente",
        "queue", "fila", "priority", "prioridade", "glpi",
        "jira", "zendesk", "freshdesk", "complaint", "reclamacao",
        "reclamação", "satisfaction", "csat", "nps",
    ],
    DataDomain.LEGAL: [
        "contract", "contrato", "clause", "clausula", "cláusula",
        "legal", "juridico", "jurídico", "compliance", "audit",
        "auditoria", "regulation", "regulacao", "regulação",
        "law", "lei", "penalty", "multa", "litigation",
        "processo", "lawsuit", "term", "term_sheet",
    ],
    DataDomain.ERP: [
        "erp", "sap", "totvs", "protheus", "oracle", "nfe",
        "nota_fiscal", "nota fiscal", "fiscal", "cfop", "ncm",
        "cnpj", "cpf", "supplier", "fornecedor", "purchase",
        "compra", "procurement", "requisition", "requisicao",
        "requisição", "production", "producao", "produção",
        "bom", "mrp", "wms", "oms",
    ],
    DataDomain.OPERATIONS: [
        "operation", "operacao", "operação", "process", "processo",
        "task", "tarefa", "workflow", "approval", "aprovacao",
        "aprovação", "sla", "kpi", "metric", "metrica", "métrica",
        "performance", "efficiency", "eficiencia", "eficiência",
        "capacity", "capacidade", "maintenance", "manutencao",
        "manutenção",
    ],
}


@dataclass
class DomainClassification:
    domain: DataDomain
    confidence: float
    signals_found: List[str] = field(default_factory=list)
    all_scores: Dict[str, float] = field(default_factory=dict)


class SemanticEngine:
    """
    Classifies datasets into business domains automatically.

    Usage:
        engine = SemanticEngine()
        classification = engine.classify(dataset_info)
        print(classification.domain)        # DataDomain.FINANCIAL
        print(classification.confidence)    # 0.87
        print(classification.signals_found) # ['invoice', 'payment', 'revenue']
    """

    def __init__(self, llm_fallback: bool = True):
        self._llm_fallback = llm_fallback

    def classify(self, dataset: DatasetInfo) -> DomainClassification:
        """
        Classify a single dataset by its name and column names.
        Returns the best matching domain with confidence score.
        """
        tokens = self._extract_tokens(dataset)
        scores = self._score_domains(tokens)
        best_domain, best_score = max(scores.items(), key=lambda x: x[1])

        signals = self._get_matched_signals(tokens, best_domain)

        # If confidence is too low and LLM fallback is enabled
        if best_score < 0.2 and self._llm_fallback:
            logger.info(f"Low confidence ({best_score:.2f}) for '{dataset.name}', trying LLM fallback")
            llm_result = self._llm_classify(dataset)
            if llm_result:
                return llm_result

        domain = DataDomain(best_domain) if best_score > 0.05 else DataDomain.UNKNOWN
        return DomainClassification(
            domain=domain,
            confidence=round(best_score, 3),
            signals_found=signals,
            all_scores={k: round(v, 3) for k, v in scores.items()},
        )

    def classify_all(self, datasets: List[DatasetInfo]) -> Dict[str, DomainClassification]:
        """Classify a list of datasets and return a dict keyed by dataset name."""
        results = {}
        for ds in datasets:
            classification = self.classify(ds)
            ds.domain = classification.domain
            ds.domain_confidence = classification.confidence
            ds.domain_signals = classification.signals_found
            results[ds.name] = classification
            logger.info(
                f"  [{ds.name}] → {classification.domain.value} "
                f"(conf={classification.confidence:.2f}, signals={classification.signals_found[:3]})"
            )
        return results

    def _extract_tokens(self, dataset: DatasetInfo) -> List[str]:
        """Extract lowercased tokens from table name + column names."""
        raw = [dataset.name] + [col.name for col in dataset.columns]
        tokens = []
        for text in raw:
            # Split camelCase, snake_case, PascalCase, spaces
            parts = re.sub(r"([A-Z])", r"_\1", text).lower()
            parts = re.split(r"[^a-záàâãéèêíïóôõöúüçñ0-9]", parts)
            tokens.extend([p for p in parts if len(p) > 1])
        return tokens

    def _score_domains(self, tokens: List[str]) -> Dict[str, float]:
        """
        Score each domain by how many of its signals appear in the tokens.
        Normalized by total signal matches to get a 0–1 confidence.
        """
        scores: Dict[str, float] = {d.value: 0.0 for d in DataDomain if d != DataDomain.UNKNOWN}
        total_matches = 0

        for domain, signals in _DOMAIN_SIGNALS.items():
            matches = 0
            for signal in signals:
                signal_tokens = signal.lower().split("_")
                if any(t in tokens for t in signal_tokens):
                    matches += 1
            scores[domain.value] = matches
            total_matches += matches

        if total_matches > 0:
            scores = {k: v / total_matches for k, v in scores.items()}

        return scores

    def _get_matched_signals(self, tokens: List[str], domain_value: str) -> List[str]:
        """Return the actual signals that matched for a given domain."""
        domain = DataDomain(domain_value)
        if domain not in _DOMAIN_SIGNALS:
            return []
        matched = []
        for signal in _DOMAIN_SIGNALS[domain]:
            signal_tokens = signal.lower().split("_")
            if any(t in tokens for t in signal_tokens):
                matched.append(signal)
        return matched[:10]

    def _llm_classify(self, dataset: DatasetInfo) -> Optional[DomainClassification]:
        """
        LLM-based fallback classification for ambiguous datasets.
        Uses a fast, cheap prompt to avoid token waste.
        """
        try:
            import sys
            from pathlib import Path as _P
            _root = str(_P(__file__).parent.parent)
            if _root not in sys.path:
                sys.path.insert(0, _root)
            from core.llm_client import LLMClient

            llm = LLMClient()
            col_names = [c.name for c in dataset.columns[:20]]
            domains_list = ", ".join([d.value for d in DataDomain if d != DataDomain.UNKNOWN])

            prompt = (
                f"You are a data analyst. Given the table name and columns below, "
                f"classify this dataset into exactly ONE business domain from this list: {domains_list}.\n\n"
                f"Table name: {dataset.name}\n"
                f"Columns: {', '.join(col_names)}\n\n"
                f"Respond with only the domain name, nothing else."
            )

            resp = llm.chat(user=prompt, max_tokens=20, temperature=0)
            domain_str = resp.content.strip().lower()

            try:
                domain = DataDomain(domain_str)
                return DomainClassification(
                    domain=domain,
                    confidence=0.7,
                    signals_found=["llm_classified"],
                )
            except ValueError:
                logger.warning(f"LLM returned unknown domain: {domain_str}")
                return None
        except Exception as e:
            logger.warning(f"LLM classify fallback failed: {e}")
            return None
