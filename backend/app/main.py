"""API FastAPI para la revision de comisiones comerciales mensuales."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.data.config_defaults import get_default_config, merge_config
from app.models.schemas import AnalyzeResponse
from app.services.commission_engine import analizar
from app.services.excel_reader import build_rows, infer_mes_anio, read_excel
from app.services.excel_writer import build_output_filename, build_workbook

app = FastAPI(
    title="Revision de Comisiones Comerciales",
    description=(
        "Backend para revisar comisiones comerciales mensuales a partir de un "
        "Excel de ventas: calcula concursos, comisiones, rappels, bonus y "
        "diferencias, y genera un Excel final de revision."
    ),
    version="1.0.0",
)

# CORS para el frontend. Orígenes locales + el dominio de producción en Fly.
# Se pueden añadir más mediante la variable de entorno CORS_ORIGINS (separados
# por comas), igual que en el proyecto de bancos.
_default_origins = [
    "http://localhost:5173",
    "http://localhost:5180",
    "http://localhost:3000",
    "https://comisiones-loangia-web.fly.dev",
]
_env_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _env_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    """Health check para el proveedor de hosting (Fly)."""
    return {"status": "ok"}

# Directorio temporal para los Excel generados.
TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp")
os.makedirs(TMP_DIR, exist_ok=True)


@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "ok", "service": "revision-comisiones"}


@app.get("/api/config/defaults")
def config_defaults() -> Dict[str, Any]:
    """Devuelve la configuracion por defecto editable."""
    return get_default_config()


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    file: UploadFile = File(...),
    config: Optional[str] = Form(None),
    mes: Optional[int] = Form(None),
    anio: Optional[int] = Form(None),
) -> AnalyzeResponse:
    """Analiza el Excel de ventas y genera el Excel de revision.

    - ``file``: archivo Excel de ventas.
    - ``config``: JSON opcional con la configuracion editable.
    - ``mes`` / ``anio``: opcionales; si no se pasan se infieren del Excel.
    """
    # Validar extension.
    filename = file.filename or "ventas.xlsx"
    if not filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx/.xls).")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo esta vacio.")

    # Parsear configuracion opcional.
    overrides: Dict[str, Any] = {}
    if config:
        try:
            overrides = json.loads(config)
            if not isinstance(overrides, dict):
                raise ValueError("La configuracion debe ser un objeto JSON.")
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Configuracion JSON invalida: {exc}")

    if mes is not None:
        overrides["mes_revision"] = mes
    if anio is not None:
        overrides["anio_revision"] = anio

    cfg = merge_config(overrides)

    # Leer Excel.
    try:
        df, mapping, inc_lectura = read_excel(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    rows, inc_filas = build_rows(df, mapping)

    # Determinar mes/anio de revision.
    mes_rev = cfg.get("mes_revision")
    anio_rev = cfg.get("anio_revision")
    if mes_rev is None or anio_rev is None:
        mes_inf, anio_inf = infer_mes_anio(rows)
        mes_rev = mes_rev or mes_inf
        anio_rev = anio_rev or anio_inf
    # Fallback al mes anterior al actual si no hay nada.
    if mes_rev is None or anio_rev is None:
        hoy = datetime.now()
        mes_anterior = hoy.month - 1 or 12
        anio_anterior = hoy.year if hoy.month > 1 else hoy.year - 1
        mes_rev = mes_rev or mes_anterior
        anio_rev = anio_rev or anio_anterior

    # Calcular.
    resultados, pareja, inc_calculo = analizar(rows, cfg)

    incidencias = inc_lectura + inc_filas + inc_calculo

    # Generar Excel.
    nombre_logico = build_output_filename(int(mes_rev), int(anio_rev))
    token = uuid.uuid4().hex[:12]
    nombre_temporal = f"{token}__{nombre_logico}"
    output_path = os.path.join(TMP_DIR, nombre_temporal)
    build_workbook(resultados, pareja, incidencias, cfg, output_path)

    # Construir resumen JSON ordenado.
    resumen = [r.model_dump(exclude={"filas"}) for r in resultados.values()]

    return AnalyzeResponse(
        mes_revision=int(mes_rev),
        anio_revision=int(anio_rev),
        nombre_archivo=nombre_temporal,
        config_usada=cfg,
        resumen=resumen,
        pareja=pareja,
        incidencias=incidencias,
        total_comerciales=len(resultados),
        total_ventas_procesadas=len(rows),
    )


@app.get("/api/download/{filename}")
def download(filename: str) -> FileResponse:
    """Devuelve el Excel final generado."""
    # Evitar path traversal.
    safe_name = os.path.basename(filename)
    path = os.path.join(TMP_DIR, safe_name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado o expirado.")
    # Nombre amigable: quitar el token "<hex>__".
    download_name = safe_name.split("__", 1)[-1] if "__" in safe_name else safe_name
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=download_name,
    )
