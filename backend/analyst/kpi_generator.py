"""
Sprint 5 — KPI Generator

Automatically generates domain-aware KPIs from a DataFrame.
No LLM required — pure statistical computation.

Domain → KPI mappings:
  financial   → total_revenue, avg_ticket, payment_rate, overdue_rate
  ecommerce   → total_orders, total_revenue, avg_order_value, top_product
  hr          → headcount, avg_salary, turnover_rate
  crm         → total_customers, active_customers, churn_rate, avg_ltv
  logistics   → total_shipments, on_time_rate, avg_delivery_days
  marketing   → total_leads, conversion_rate, cac
  (any)       → row_count, column_count, null_rate, duplicate_rate
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class KPI:
    name: str
    value: Any
    unit: str = ""
    trend: Optional[str] = None          # "up" | "down" | "stable" | None
    trend_pct: Optional[float] = None
    status: str = "info"                 # "good" | "warning" | "critical" | "info"
    description: str = ""
    domain: str = "generic"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "trend": self.trend,
            "trend_pct": self.trend_pct,
            "status": self.status,
            "description": self.description,
            "domain": self.domain,
        }


# ---------------------------------------------------------------------------
# Column pattern matchers — used to auto-detect semantic columns
# ---------------------------------------------------------------------------

def _find_col(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    """Return first column matching any pattern (case-insensitive)."""
    for pat in patterns:
        regex = re.compile(pat, re.IGNORECASE)
        for col in df.columns:
            if regex.search(col):
                return col
    return None


_REVENUE_COLS = [r"revenue", r"receita", r"valor", r"amount", r"total", r"price", r"preco"]
_DATE_COLS    = [r"date", r"data", r"created", r"at$", r"time"]
_STATUS_COLS  = [r"status", r"estado", r"situacao"]
_CUSTOMER_COLS = [r"customer", r"client", r"cliente", r"company"]
_PRODUCT_COLS  = [r"product", r"produto", r"item", r"sku"]
_QTY_COLS      = [r"qty", r"quantity", r"quantidade", r"units"]
_SALARY_COLS   = [r"salary", r"salario", r"wage", r"remuner"]
_NAME_COLS     = [r"name", r"nome", r"employee", r"funcionario"]
_LEAD_COLS     = [r"lead", r"prospect", r"contact", r"contato"]
_CONV_COLS     = [r"converted", r"conversion", r"won", r"fechado"]


class KPIGenerator:
    """
    Generates KPIs from a DataFrame given a business domain hint.

    Usage:
        gen = KPIGenerator()
        kpis = gen.generate(df, domain="financial", source_name="Sales")
    """

    def generate(
        self,
        df: pd.DataFrame,
        domain: str = "unknown",
        source_name: str = "dataset",
    ) -> List[KPI]:
        kpis: List[KPI] = []

        # Always: generic dataset stats
        kpis.extend(self._generic_kpis(df, source_name))

        # Domain-specific
        generators = {
            "financial": self._financial_kpis,
            "ecommerce": self._ecommerce_kpis,
            "hr":        self._hr_kpis,
            "crm":       self._crm_kpis,
            "logistics": self._logistics_kpis,
            "marketing": self._marketing_kpis,
        }
        gen_fn = generators.get(domain)
        if gen_fn:
            try:
                kpis.extend(gen_fn(df, source_name))
            except Exception as e:
                logger.warning(f"Domain KPI generation failed ({domain}): {e}")
        else:
            # Unknown domain: try to infer from column patterns
            kpis.extend(self._inferred_kpis(df, source_name))

        return kpis

    # ------------------------------------------------------------------
    # Generic
    # ------------------------------------------------------------------

    def _generic_kpis(self, df: pd.DataFrame, name: str) -> List[KPI]:
        kpis = []
        null_pct = df.isnull().sum().sum() / max(df.size, 1)
        dup_pct = df.duplicated().sum() / max(len(df), 1)

        kpis.append(KPI(
            name="Total de Registros",
            value=len(df),
            unit="linhas",
            status="info",
            description=f"Total de registros em '{name}'",
        ))
        kpis.append(KPI(
            name="Taxa de Nulos",
            value=round(null_pct * 100, 1),
            unit="%",
            status="good" if null_pct < 0.05 else "warning" if null_pct < 0.2 else "critical",
            description="Percentual de valores ausentes no dataset",
        ))
        if dup_pct > 0:
            kpis.append(KPI(
                name="Linhas Duplicadas",
                value=int(df.duplicated().sum()),
                unit="linhas",
                status="warning" if dup_pct < 0.05 else "critical",
                description=f"{dup_pct:.1%} de duplicatas detectadas",
            ))
        return kpis

    # ------------------------------------------------------------------
    # Financial
    # ------------------------------------------------------------------

    def _financial_kpis(self, df: pd.DataFrame, name: str) -> List[KPI]:
        kpis = []
        rev_col = _find_col(df, _REVENUE_COLS)
        status_col = _find_col(df, _STATUS_COLS)
        customer_col = _find_col(df, _CUSTOMER_COLS)

        if rev_col:
            rev = pd.to_numeric(df[rev_col], errors="coerce").dropna()
            if len(rev) > 0:
                total = rev.sum()
                avg = rev.mean()
                kpis.append(KPI(
                    name="Receita Total",
                    value=round(float(total), 2),
                    unit="R$",
                    status="info",
                    description=f"Soma de {rev_col}",
                    domain="financial",
                ))
                kpis.append(KPI(
                    name="Ticket Médio",
                    value=round(float(avg), 2),
                    unit="R$",
                    status="info",
                    description=f"Média de {rev_col} por registro",
                    domain="financial",
                ))
                kpis.append(KPI(
                    name="Maior Valor",
                    value=round(float(rev.max()), 2),
                    unit="R$",
                    status="info",
                    description=f"Valor máximo em {rev_col}",
                    domain="financial",
                ))

        if status_col:
            vc = df[status_col].str.lower().value_counts(normalize=True)
            paid_rate = sum(v for k, v in vc.items() if "paid" in str(k) or "pago" in str(k))
            if paid_rate > 0:
                kpis.append(KPI(
                    name="Taxa de Pagamento",
                    value=round(paid_rate * 100, 1),
                    unit="%",
                    status="good" if paid_rate > 0.8 else "warning" if paid_rate > 0.5 else "critical",
                    description="Percentual de registros com status pago",
                    domain="financial",
                ))

        if customer_col:
            n_customers = df[customer_col].nunique()
            kpis.append(KPI(
                name="Clientes Únicos",
                value=n_customers,
                unit="clientes",
                status="info",
                description=f"Clientes distintos em {customer_col}",
                domain="financial",
            ))
            if rev_col:
                rev_by_customer = df.groupby(customer_col)[rev_col].sum()
                top_customer = rev_by_customer.idxmax()
                top_value = round(float(rev_by_customer.max()), 2)
                top_share = round(float(rev_by_customer.max() / rev_by_customer.sum() * 100), 1)
                kpis.append(KPI(
                    name="Top Cliente",
                    value=str(top_customer),
                    unit="",
                    status="warning" if top_share > 50 else "info",
                    description=f"Maior cliente: R$ {top_value:,.2f} ({top_share}% da receita)",
                    domain="financial",
                ))

        return kpis

    # ------------------------------------------------------------------
    # E-commerce
    # ------------------------------------------------------------------

    def _ecommerce_kpis(self, df: pd.DataFrame, name: str) -> List[KPI]:
        kpis = self._financial_kpis(df, name)  # reuse financial
        product_col = _find_col(df, _PRODUCT_COLS)
        qty_col = _find_col(df, _QTY_COLS)

        if product_col:
            top_product = df[product_col].value_counts().idxmax()
            kpis.append(KPI(
                name="Produto Mais Vendido",
                value=str(top_product),
                unit="",
                status="info",
                description=f"Produto com mais pedidos em {product_col}",
                domain="ecommerce",
            ))

        if qty_col:
            qty = pd.to_numeric(df[qty_col], errors="coerce").dropna()
            kpis.append(KPI(
                name="Volume Total",
                value=int(qty.sum()),
                unit="unidades",
                status="info",
                description=f"Total de unidades em {qty_col}",
                domain="ecommerce",
            ))
        return kpis

    # ------------------------------------------------------------------
    # HR
    # ------------------------------------------------------------------

    def _hr_kpis(self, df: pd.DataFrame, name: str) -> List[KPI]:
        kpis = []
        name_col = _find_col(df, _NAME_COLS)
        salary_col = _find_col(df, _SALARY_COLS)

        kpis.append(KPI(
            name="Headcount",
            value=len(df),
            unit="funcionários",
            status="info",
            description="Total de funcionários no dataset",
            domain="hr",
        ))

        if salary_col:
            sal = pd.to_numeric(df[salary_col], errors="coerce").dropna()
            if len(sal) > 0:
                kpis.append(KPI(
                    name="Salário Médio",
                    value=round(float(sal.mean()), 2),
                    unit="R$",
                    status="info",
                    description=f"Média salarial",
                    domain="hr",
                ))
                kpis.append(KPI(
                    name="Folha Total",
                    value=round(float(sal.sum()), 2),
                    unit="R$",
                    status="info",
                    description="Custo total de salários",
                    domain="hr",
                ))
        return kpis

    # ------------------------------------------------------------------
    # CRM
    # ------------------------------------------------------------------

    def _crm_kpis(self, df: pd.DataFrame, name: str) -> List[KPI]:
        return self._financial_kpis(df, name)

    # ------------------------------------------------------------------
    # Logistics
    # ------------------------------------------------------------------

    def _logistics_kpis(self, df: pd.DataFrame, name: str) -> List[KPI]:
        kpis = []
        kpis.append(KPI(
            name="Total de Envios",
            value=len(df),
            unit="envios",
            status="info",
            description="Volume total de envios/pedidos",
            domain="logistics",
        ))
        status_col = _find_col(df, _STATUS_COLS)
        if status_col:
            vc = df[status_col].str.lower().value_counts(normalize=True)
            delivered = sum(v for k, v in vc.items()
                           if any(w in str(k) for w in ("deliv", "entregue", "conclu")))
            if delivered > 0:
                kpis.append(KPI(
                    name="Taxa de Entrega",
                    value=round(delivered * 100, 1),
                    unit="%",
                    status="good" if delivered > 0.9 else "warning",
                    description="Percentual de envios entregues",
                    domain="logistics",
                ))
        return kpis

    # ------------------------------------------------------------------
    # Marketing
    # ------------------------------------------------------------------

    def _marketing_kpis(self, df: pd.DataFrame, name: str) -> List[KPI]:
        kpis = []
        kpis.append(KPI(
            name="Total de Leads",
            value=len(df),
            unit="leads",
            status="info",
            description="Volume total de leads/contatos",
            domain="marketing",
        ))
        conv_col = _find_col(df, _CONV_COLS)
        if conv_col:
            conv_rate = df[conv_col].astype(str).str.lower().isin(
                ["true", "1", "yes", "sim", "won", "converted"]
            ).mean()
            kpis.append(KPI(
                name="Taxa de Conversão",
                value=round(conv_rate * 100, 1),
                unit="%",
                status="good" if conv_rate > 0.2 else "warning" if conv_rate > 0.1 else "critical",
                description="Percentual de leads convertidos",
                domain="marketing",
            ))
        return kpis

    # ------------------------------------------------------------------
    # Inferred (unknown domain)
    # ------------------------------------------------------------------

    def _inferred_kpis(self, df: pd.DataFrame, name: str) -> List[KPI]:
        kpis = []
        rev_col = _find_col(df, _REVENUE_COLS)
        if rev_col:
            kpis.extend(self._financial_kpis(df, name))
        return kpis
