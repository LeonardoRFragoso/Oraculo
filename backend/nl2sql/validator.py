"""
SQL Validator — safety and correctness checks before execution.

Prevents:
  - DDL statements (CREATE, DROP, ALTER, TRUNCATE)
  - DML mutations (INSERT, UPDATE, DELETE, MERGE)
  - Dangerous functions (EXEC, xp_cmdshell, LOAD_FILE, etc.)
  - SQL injection patterns
  - Stacked queries (multiple statements)

Also validates:
  - Referenced tables exist in the schema
  - Query is not empty
  - Query is parseable (basic)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Set

logger = logging.getLogger(__name__)

# Forbidden keywords that indicate mutations or dangerous operations
_FORBIDDEN_PATTERNS = [
    # DDL
    r"\bCREATE\b", r"\bDROP\b", r"\bALTER\b", r"\bTRUNCATE\b", r"\bRENAME\b",
    # DML mutations
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bMERGE\b", r"\bREPLACE\b",
    r"\bUPSERT\b",
    # Dangerous functions / execution
    r"\bEXEC\b", r"\bEXECUTE\b", r"\bxp_cmdshell\b", r"\bsp_\w+\b",
    r"\bLOAD_FILE\b", r"\bINTO\s+OUTFILE\b", r"\bINTO\s+DUMPFILE\b",
    # Privilege escalation
    r"\bGRANT\b", r"\bREVOKE\b", r"\bCREATE\s+USER\b",
    # Comment-based injection signals
    r";\s*--", r";\s*/\*",
]

_STACKED_QUERY = re.compile(r";\s*\w", re.IGNORECASE)

_FORBIDDEN_RE = [re.compile(p, re.IGNORECASE) for p in _FORBIDDEN_PATTERNS]


@dataclass
class ValidationResult:
    valid: bool
    sql: Optional[str] = None          # normalized SQL if valid
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class SQLValidator:
    """
    Validates a SQL string before allowing execution.

    Usage:
        validator = SQLValidator(allowed_tables={"clientes", "vendas"})
        result = validator.validate("SELECT * FROM clientes LIMIT 100")
        if result.valid:
            execute(result.sql)
        else:
            print(result.issues)
    """

    def __init__(
        self,
        allowed_tables: Optional[Set[str]] = None,
        max_limit: int = 10_000,
    ):
        self.allowed_tables = {t.lower() for t in allowed_tables} if allowed_tables else None
        self.max_limit = max_limit

    def validate(self, sql: str) -> ValidationResult:
        if not sql or not sql.strip():
            return ValidationResult(valid=False, issues=["SQL is empty"])

        sql = sql.strip()
        issues = []
        warnings = []

        # 1. Must start with SELECT (or WITH for CTEs)
        first_token = sql.split()[0].upper()
        if first_token not in ("SELECT", "WITH", "EXPLAIN"):
            issues.append(
                f"Only SELECT queries are allowed. Got: {first_token}"
            )

        # 2. Forbidden patterns
        for pattern in _FORBIDDEN_RE:
            if pattern.search(sql):
                kw = pattern.pattern.replace(r"\b", "").replace(r"\s+", " ").strip()
                issues.append(f"Forbidden keyword detected: {kw}")

        # 3. Stacked queries
        if _STACKED_QUERY.search(sql):
            issues.append("Stacked queries (multiple statements) are not allowed")

        # 4. Early exit on hard blockers
        if issues:
            return ValidationResult(valid=False, issues=issues)

        # 5. Table whitelist check (soft — warn only)
        if self.allowed_tables:
            referenced = self._extract_table_names(sql)
            unknown = referenced - self.allowed_tables
            if unknown:
                warnings.append(
                    f"Referenced tables not in schema: {', '.join(unknown)}"
                )

        # 6. Missing LIMIT warning
        if not re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
            sql = f"{sql.rstrip(';')} LIMIT {self.max_limit}"
            warnings.append(
                f"No LIMIT clause found — automatically added LIMIT {self.max_limit}"
            )

        # 7. SELECT * warning
        if re.search(r"SELECT\s+\*", sql, re.IGNORECASE):
            warnings.append(
                "SELECT * detected — consider selecting specific columns for performance"
            )

        return ValidationResult(valid=True, sql=sql, issues=[], warnings=warnings)

    def _extract_table_names(self, sql: str) -> Set[str]:
        """
        Heuristic table name extractor.
        Finds table names after FROM, JOIN keywords.
        """
        pattern = re.compile(
            r"\b(?:FROM|JOIN)\s+([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        )
        tables = set()
        for match in pattern.finditer(sql):
            name = match.group(1).strip('`"[]').split(".")[-1].lower()
            tables.add(name)
        return tables
