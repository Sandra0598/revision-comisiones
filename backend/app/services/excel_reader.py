"""Lectura del Excel de ventas y normalizacion de filas a campos internos."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.models.schemas import Incidencia
from app.services.column_mapper import map_columns, missing_required
from app.utils.normalize import motivo_descarte_fila, normalize_amount, normalize_text


def read_excel(content: bytes) -> Tuple[pd.DataFrame, Dict[str, Optional[str]], List[Incidencia]]:
    """Lee el Excel desde bytes y devuelve (df_crudo, mapeo_columnas, incidencias)."""
    incidencias: List[Incidencia] = []
    try:
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"No se pudo leer el Excel: {exc}") from exc

    # Eliminar columnas y filas totalmente vacias.
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    df.columns = [str(c).strip() for c in df.columns]

    mapping = map_columns(list(df.columns))

    for field in missing_required(mapping):
        incidencias.append(
            Incidencia(
                tipo="columna_imprescindible_faltante",
                descripcion=(
                    f"No se encontro la columna imprescindible '{field}'. "
                    "El analisis puede ser incompleto."
                ),
                gravedad="alta",
            )
        )

    return df, mapping, incidencias


def _parse_fecha(value: Any) -> Optional[datetime]:
    """Intenta convertir un valor a datetime."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value
    try:
        ts = pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.to_pydatetime()
    except Exception:  # noqa: BLE001
        return None


def build_rows(
    df: pd.DataFrame, mapping: Dict[str, Optional[str]]
) -> Tuple[List[Dict[str, Any]], List[Incidencia]]:
    """Convierte el DataFrame crudo en filas normalizadas con campos internos.

    Cada fila incluye ``_fila_original`` (1-indexada respecto a los datos) para
    poder rastrear incidencias.
    """
    incidencias: List[Incidencia] = []
    rows: List[Dict[str, Any]] = []
    descartes: Dict[str, int] = {}

    def col(field: str) -> Optional[str]:
        return mapping.get(field)

    for idx, (_, raw) in enumerate(df.iterrows(), start=1):
        def get(field: str) -> Any:
            c = col(field)
            if c is None:
                return None
            val = raw.get(c)
            if isinstance(val, float) and pd.isna(val):
                return None
            return val

        comercial_raw = get("comercial")
        importe_raw = get("importe_venta")
        importe = normalize_amount(importe_raw)

        # Filas que no son ventas reales (abonos, ventas no validas, regalos,
        # bajas sin importe): se descartan por completo, sin contabilizarlas ni
        # generar incidencias de "venta sin comercial/importe".
        motivo = motivo_descarte_fila(get("estado"), get("tipo_venta"), importe)
        if motivo is not None:
            descartes[motivo] = descartes.get(motivo, 0) + 1
            continue

        row: Dict[str, Any] = {
            "_fila_original": idx,
            "comercial": str(comercial_raw).strip() if comercial_raw is not None else None,
            "fecha_venta": _parse_fecha(get("fecha_venta")),
            "cliente": str(get("cliente")).strip() if get("cliente") is not None else None,
            "tipo_venta": get("tipo_venta"),
            "pizarra": get("pizarra"),
            "importe_venta": importe,
            "importe_venta_original": importe_raw,
            "comision_declarada": normalize_amount(get("comision_declarada")),
            "producto": get("producto"),
            "servicio_contratado": get("servicio_contratado"),
            "observaciones": get("observaciones"),
            "estado": get("estado"),
        }

        # Validaciones a nivel de fila.
        if row["comercial"] is None or normalize_text(row["comercial"]) == "":
            incidencias.append(
                Incidencia(
                    fila_original=idx,
                    tipo="venta_sin_comercial",
                    descripcion="Venta sin comercial asignada.",
                    gravedad="alta",
                )
            )
        if importe is None and importe_raw is not None:
            incidencias.append(
                Incidencia(
                    fila_original=idx,
                    comercial=row["comercial"],
                    tipo="importe_no_reconocible",
                    descripcion=f"Importe no reconocible: '{importe_raw}'.",
                    gravedad="media",
                )
            )
        elif importe is None and importe_raw is None:
            incidencias.append(
                Incidencia(
                    fila_original=idx,
                    comercial=row["comercial"],
                    tipo="venta_sin_importe",
                    descripcion="Venta sin importe.",
                    gravedad="media",
                )
            )

        rows.append(row)

    if descartes:
        etiquetas = {
            "abono": "abonos",
            "venta_no_valida": "ventas no validas",
            "regalo": "regalos",
            "baja_sin_importe": "bajas sin importe",
        }
        detalle = ", ".join(
            f"{n} {etiquetas.get(motivo, motivo)}" for motivo, n in sorted(descartes.items())
        )
        total = sum(descartes.values())
        incidencias.append(
            Incidencia(
                tipo="filas_excluidas",
                descripcion=(
                    f"Se excluyeron {total} fila(s) que no son ventas reales "
                    f"({detalle}); no se contabilizan en ventas, carteras ni "
                    "comisiones."
                ),
                gravedad="baja",
            )
        )

    return rows, incidencias


def infer_mes_anio(rows: List[Dict[str, Any]]) -> Tuple[Optional[int], Optional[int]]:
    """Infiere mes/anio a partir de la fecha mas frecuente en las ventas."""
    fechas = [r["fecha_venta"] for r in rows if r.get("fecha_venta")]
    if not fechas:
        return None, None
    # Tomar el (mes, anio) mas frecuente.
    conteo: Dict[Tuple[int, int], int] = {}
    for f in fechas:
        key = (f.month, f.year)
        conteo[key] = conteo.get(key, 0) + 1
    (mes, anio) = max(conteo.items(), key=lambda kv: kv[1])[0]
    return mes, anio
