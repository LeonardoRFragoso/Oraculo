"""
Data Sources Router — Sprint 1 endpoints

POST   /api/datasources          Register a new source
GET    /api/datasources          List all sources
GET    /api/datasources/{id}     Get source details
POST   /api/datasources/{id}/connect   Trigger discovery
DELETE /api/datasources/{id}     Remove source
GET    /api/datasources/catalog/summary  Domain distribution
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

# Ensure project root is on sys.path when running from backend/
_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from connectors.base import ConnectorType
from catalog.registry import DataSourceRegistry
from catalog.schema_discovery import SchemaDiscovery

logger = logging.getLogger(__name__)
router = APIRouter()

# Singletons — will be replaced by DI in Sprint 7
_registry = DataSourceRegistry()
_discovery = SchemaDiscovery(registry=_registry)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RegisterSourceRequest(BaseModel):
    name: str
    connector_type: str
    config: Dict[str, Any]
    description: Optional[str] = None
    tags: List[str] = []


class RegisterSourceResponse(BaseModel):
    id: str
    name: str
    connector_type: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/datasources", response_model=RegisterSourceResponse, status_code=201)
async def register_datasource(request: RegisterSourceRequest):
    """
    Register a new data source.

    Examples:

    SQLite:
        {"name": "MyDB", "connector_type": "sqlite", "config": {"path": "/data/mydb.sqlite"}}

    PostgreSQL:
        {"name": "Prod DB", "connector_type": "postgresql",
         "config": {"host": "localhost", "port": 5432, "database": "mydb",
                    "user": "postgres", "password": "secret"}}

    CSV:
        {"name": "Sales 2025", "connector_type": "csv", "config": {"path": "/uploads/sales.csv"}}
    """
    try:
        ctype = ConnectorType(request.connector_type.lower())
    except ValueError:
        valid = [t.value for t in ConnectorType]
        raise HTTPException(
            status_code=400,
            detail=f"Unknown connector_type '{request.connector_type}'. Valid: {valid}",
        )

    record = _registry.register(
        name=request.name,
        connector_type=ctype,
        config=request.config,
        description=request.description,
        tags=request.tags,
    )

    return RegisterSourceResponse(
        id=record.id,
        name=record.name,
        connector_type=record.connector_type,
        status=record.status,
        message=f"Source '{record.name}' registered. Call POST /api/datasources/{record.id}/connect to run discovery.",
    )


@router.post("/datasources/upload", response_model=RegisterSourceResponse, status_code=201)
async def upload_and_register(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
):
    """
    Upload a file and automatically register it as a data source.
    Supports: CSV, XLSX, XLS, JSON, Parquet, PDF, DOCX, TXT, XML.
    """
    import uuid
    from pathlib import Path as P

    ext = P(file.filename).suffix.lower()
    ext_to_type = {
        ".csv": ConnectorType.CSV,
        ".xlsx": ConnectorType.EXCEL,
        ".xls": ConnectorType.EXCEL,
        ".json": ConnectorType.JSON,
        ".parquet": ConnectorType.PARQUET,
        ".pdf": ConnectorType.PDF,
        ".docx": ConnectorType.DOCX,
        ".txt": ConnectorType.TXT,
        ".xml": ConnectorType.XML,
    }
    ctype = ext_to_type.get(ext)
    if not ctype:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    upload_dir = P("../dados/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = upload_dir / f"{file_id}{ext}"
    content = await file.read()
    file_path.write_bytes(content)

    source_name = name or P(file.filename).stem
    record = _registry.register(
        name=source_name,
        connector_type=ctype,
        config={"path": str(file_path)},
        description=f"Uploaded file: {file.filename}",
        tags=["uploaded"],
    )

    return RegisterSourceResponse(
        id=record.id,
        name=record.name,
        connector_type=record.connector_type,
        status=record.status,
        message=f"File uploaded and registered. Call POST /api/datasources/{record.id}/connect to discover schema.",
    )


@router.post("/datasources/{source_id}/connect")
async def connect_and_discover(source_id: str):
    """
    Trigger schema discovery + Semantic Engine classification for a source.

    This endpoint:
    1. Connects to the source
    2. Discovers all tables / sheets / structure
    3. Classifies each dataset into a business domain (Fase 0)
    4. Persists the catalog entry
    5. Returns a full discovery report
    """
    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    report = _discovery.discover(source_id)

    if not report.success:
        raise HTTPException(status_code=422, detail=report.error)

    return {
        "source_id": report.source_id,
        "source_name": report.source_name,
        "connector_type": report.connector_type,
        "total_tables": report.total_tables,
        "total_rows": report.total_rows,
        "domain_summary": report.domain_summary,
        "domain_classifications": report.domain_classifications,
        "datasets": report.datasets,
    }


@router.get("/datasources")
async def list_datasources(owner_id: Optional[str] = None):
    """List all registered data sources."""
    sources = _registry.list(owner_id=owner_id)
    return {
        "total": len(sources),
        "sources": [s.to_dict() for s in sources],
    }


@router.get("/datasources/catalog/summary")
async def catalog_summary(owner_id: Optional[str] = None):
    """Return domain distribution across all connected sources."""
    return _registry.get_domain_summary(owner_id=owner_id)


@router.get("/datasources/actions/catalog")
async def list_actions():
    """Sprint 6 — List all available Oracle Actions."""
    import actions.builtin  # noqa: F401 — triggers registration
    from actions.registry import registry as _action_registry
    return {"actions": _action_registry.list_all()}


@router.get("/datasources/alerts")
async def list_alerts(limit: int = 50):
    """Sprint 6 — List recent alerts created by Oracle Actions."""
    import json
    from pathlib import Path
    alerts_file = Path("../dados/alerts/alerts.jsonl")
    if not alerts_file.exists():
        return {"alerts": [], "total": 0}
    lines = alerts_file.read_text(encoding="utf-8").strip().splitlines()
    alerts = []
    for line in lines[-limit:]:
        try:
            alerts.append(json.loads(line))
        except Exception:
            pass
    alerts.reverse()
    return {"alerts": alerts, "total": len(lines)}


@router.get("/datasources/{source_id}")
async def get_datasource(source_id: str):
    """Get full details of a registered source including discovered schema."""
    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return record.to_dict()


@router.get("/datasources/{source_id}/profile")
async def get_profile(source_id: str, dataset: Optional[str] = None):
    """
    Return detailed column-level profile for a connected source.
    Optionally filter by dataset/table name with ?dataset=table_name.
    """
    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    if record.status not in ("connected",):
        raise HTTPException(
            status_code=422,
            detail=f"Source not yet connected. Call POST /api/datasources/{source_id}/connect first.",
        )

    # Re-run profiling on demand
    from catalog.profiler import DataProfiler
    from catalog.schema_discovery import SchemaDiscovery
    disc = SchemaDiscovery(registry=_registry)
    connector = disc._build_connector(record)
    if not connector.connect():
        raise HTTPException(status_code=422, detail="Could not reconnect to source")

    result = connector.extract(dataset_name=dataset)
    connector.close()

    if not result.success:
        raise HTTPException(status_code=422, detail=result.error)

    profiler = DataProfiler()
    profiles = {}
    for ds_name, df in result.dataframes.items():
        profiles[ds_name] = profiler.profile(df.head(50_000), ds_name).to_dict()

    return {"source_id": source_id, "profiles": profiles}


@router.get("/datasources/{source_id}/quality")
async def get_quality(source_id: str):
    """
    Return Data Quality Score (0-100) for a connected source.
    Returns scores per dataset + overall grade + recommendations.
    """
    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    quality_data = record.domain_summary.get("quality")
    if not quality_data:
        raise HTTPException(
            status_code=422,
            detail=f"No quality data yet. Call POST /api/datasources/{source_id}/connect first.",
        )

    return {
        "source_id": source_id,
        "source_name": record.name,
        "quality": quality_data,
    }


@router.post("/datasources/{source_id}/analyze")
async def analyze_datasource(source_id: str):
    """
    Sprint 5 — AI Data Analyst

    Proactively analyzes a connected data source and returns:
    - Domain-aware KPIs (revenue, headcount, top products, etc.)
    - Anomaly alerts (outliers, concentration risk, time gaps, negative values)
    - Executive summary narrative

    No question needed — the system generates insights automatically.
    """
    from analyst.insight_engine import InsightEngine

    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    if record.status != "connected":
        raise HTTPException(
            status_code=422,
            detail=f"Source not connected. Call POST /api/datasources/{source_id}/connect first.",
        )

    engine = InsightEngine()
    report = engine.analyze(source_id=source_id, record=record)
    return report.to_dict()


class ActRequest(BaseModel):
    instruction: Optional[str] = None        # e.g. "Gerar relatório e enviar para cfo@corp.com"
    params: Optional[Dict[str, Any]] = None  # explicit action params override
    dry_run: bool = False                     # if True, describe but don't execute


@router.post("/datasources/{source_id}/act")
async def act_on_datasource(source_id: str, request: ActRequest):
    """
    Sprint 6 — Agent Actions

    Executes Oracle Actions on a data source based on a natural language instruction
    or automatically triggered by critical anomalies.

    Examples:
      - {"instruction": "Gerar relatório markdown"}
      - {"instruction": "Enviar email para cfo@corp.com com os alertas"}
      - {"instruction": "Criar alerta", "params": {"severity": "critical"}}
      - {"dry_run": true, "instruction": "Enviar email para time@corp.com"}

    Auto-mode (no instruction): if the source has critical anomalies,
    automatically creates an alert record.
    """
    from analyst.insight_engine import InsightEngine
    from actions.planner import ActionPlanner
    from actions.base import ActionContext

    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    if record.status != "connected":
        raise HTTPException(
            status_code=422,
            detail=f"Source not connected. Call POST /api/datasources/{source_id}/connect first.",
        )

    # Run analysis to get KPIs + anomalies for action context
    engine = InsightEngine()
    report = engine.analyze(source_id=source_id, record=record)

    all_kpis = [k for ds in report.datasets for k in [k.to_dict() for k in ds.kpis]]
    all_anomalies = [a for ds in report.datasets for a in [a.to_dict() for a in ds.anomalies]]

    ctx = ActionContext(
        trigger="user" if request.instruction else "anomaly",
        source_id=source_id,
        source_name=record.name,
        params=request.params or {},
        kpis=all_kpis,
        anomalies=all_anomalies,
        user_instruction=request.instruction,
        dry_run=request.dry_run,
    )

    planner = ActionPlanner(use_llm=True)
    plan = planner.plan_only(request.instruction, ctx)
    results = planner.plan_and_run(request.instruction, ctx)

    return {
        "source_id": source_id,
        "source_name": record.name,
        "instruction": request.instruction,
        "dry_run": request.dry_run,
        "plan": plan,
        "actions_executed": len(results),
        "results": [r.to_dict() for r in results],
        "kpi_count": len(all_kpis),
        "anomaly_count": len(all_anomalies),
    }


@router.post("/datasources/{source_id}/graph")
async def build_graph(source_id: str):
    """
    Sprint 7 — Knowledge Graph

    Builds a knowledge graph from the data source by:
    1. Extracting typed entities (CUSTOMER, PRODUCT, EMPLOYEE, LOCATION, ...)
    2. Inferring weighted relations from row co-occurrence (PURCHASED, WORKS_IN, ...)
    3. Computing centrality stats (most connected entities)

    Returns the graph + stats. Also persists to disk for fast subsequent loads.
    """
    from graph.graph_store import GraphStore

    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    if record.status != "connected":
        raise HTTPException(
            status_code=422,
            detail=f"Source not connected. Call POST /api/datasources/{source_id}/connect first.",
        )

    store = GraphStore()
    kg = store.build(source_id=source_id, record=record)
    stats = kg.compute_stats()
    graph_data = kg.get_full_graph()

    return {
        "source_id": source_id,
        "source_name": record.name,
        "stats": stats.to_dict(),
        "graph": graph_data,
    }


@router.get("/datasources/{source_id}/graph")
async def get_graph(source_id: str, max_nodes: int = 200):
    """
    Sprint 7 — Retrieve stored Knowledge Graph (built via POST /graph).
    Returns graph data ready for vis.js / D3 / Cytoscape.
    """
    from graph.graph_store import GraphStore

    record = _registry.get(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    store = GraphStore()
    if not store.has_graph(source_id):
        raise HTTPException(
            status_code=404,
            detail=f"No graph built yet. Call POST /api/datasources/{source_id}/graph first.",
        )

    kg = store.load(source_id)
    stats = kg.compute_stats()
    graph_data = kg.get_full_graph(max_nodes=max_nodes)

    return {
        "source_id": source_id,
        "source_name": record.name,
        "stats": stats.to_dict(),
        "graph": graph_data,
    }


@router.get("/datasources/{source_id}/graph/search")
async def search_graph(source_id: str, q: str, limit: int = 20):
    """Sprint 7 — Search entities in the knowledge graph by label."""
    from graph.graph_store import GraphStore

    store = GraphStore()
    if not store.has_graph(source_id):
        raise HTTPException(status_code=404, detail="No graph built yet.")

    kg = store.load(source_id)
    results = kg.search(q, limit=limit)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/datasources/{source_id}/graph/entity/{entity_id:path}")
async def get_entity(source_id: str, entity_id: str, depth: int = 1):
    """Sprint 7 — Get entity details + neighbors from the knowledge graph."""
    from graph.graph_store import GraphStore

    store = GraphStore()
    if not store.has_graph(source_id):
        raise HTTPException(status_code=404, detail="No graph built yet.")

    kg = store.load(source_id)
    entity = kg.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in graph.")

    neighbors = kg.neighbors(entity_id, depth=depth)
    return {
        "entity": entity,
        "neighbors": neighbors,
        "neighbor_count": len(neighbors),
    }


@router.delete("/datasources/{source_id}")
async def delete_datasource(source_id: str):
    """Remove a data source from the registry."""
    deleted = _registry.delete(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return {"success": True, "message": f"Source {source_id} removed"}
