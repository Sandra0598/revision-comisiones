"""Mapeo de columnas del Excel por similitud a los campos internos esperados."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from app.utils.normalize import normalize_text

# Campos internos esperados.
INTERNAL_FIELDS = [
    "comercial",
    "fecha_venta",
    "cliente",
    "tipo_venta",
    "pizarra",
    "importe_venta",
    "comision_declarada",
    "producto",
    "servicio_contratado",
    "observaciones",
    "estado",
]

# Columnas imprescindibles: si faltan, se registra incidencia.
REQUIRED_FIELDS = ["comercial", "tipo_venta", "importe_venta"]

# Sinonimos por campo (ya pensados para comparar normalizados).
SYNONYMS: Dict[str, List[str]] = {
    "comercial": ["comercial", "vendedora", "vendedor", "asesora", "asesor", "responsable", "agente"],
    "fecha_venta": ["fecha", "fecha venta", "dia", "fecha cierre", "fecha de venta", "fecha de cierre"],
    "cliente": ["cliente", "empresa", "nombre cliente", "nombre del cliente"],
    "tipo_venta": [
        "tipo",
        "tipo venta",
        "categoria",
        "categoria comercial",
        "categoria de venta",
        "categoria venta",
        "producto tipo",
        "tipo de venta",
        "tipo producto",
    ],
    "pizarra": ["pizarra", "board", "equipo", "pizarra venta", "pizarra de venta"],
    "importe_venta": ["importe", "precio", "valor", "total", "total venta", "importe venta", "importe de venta"],
    "comision_declarada": ["comision", "comision declarada", "comision comercial", "comision_declarada"],
    "producto": ["producto", "tarifa", "plan"],
    "servicio_contratado": [
        "servicio contratado",
        "servicio",
        "servicio contrato",
        "producto contratado",
    ],
    "observaciones": ["observaciones", "notas", "comentario", "comentarios", "observacion"],
    "estado": ["estado", "estado venta", "estado de la venta", "situacion", "estado operacion"],
}


def _similarity(a: str, b: str) -> float:
    """Similitud entre dos cadenas ya normalizadas (0..1)."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    # Coincidencia por subcadena bonificada.
    if a in b or b in a:
        base = 0.85
    else:
        base = 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    return max(base, ratio)


def _best_field_for_column(column_norm: str) -> Tuple[Optional[str], float]:
    """Devuelve el mejor campo interno para una columna dada y su score."""
    best_field: Optional[str] = None
    best_score = 0.0
    for field, synonyms in SYNONYMS.items():
        for syn in synonyms:
            score = _similarity(column_norm, normalize_text(syn))
            if score > best_score:
                best_score = score
                best_field = field
    return best_field, best_score


def map_columns(columns: List[str], threshold: float = 0.6) -> Dict[str, Optional[str]]:
    """Mapea las columnas reales del Excel a los campos internos.

    Devuelve un diccionario campo_interno -> nombre_columna_original (o None).
    Cada columna original se asigna como mucho a un campo (el de mayor score).
    """
    # Calcular score de cada (columna, campo) y resolver conflictos por score.
    candidates: List[Tuple[float, str, str]] = []  # (score, field, column)
    for col in columns:
        col_norm = normalize_text(col)
        if not col_norm:
            continue
        field, score = _best_field_for_column(col_norm)
        if field and score >= threshold:
            candidates.append((score, field, col))

    # Ordenar por score descendente y asignar de forma codiciosa.
    candidates.sort(key=lambda x: x[0], reverse=True)
    mapping: Dict[str, Optional[str]] = {f: None for f in INTERNAL_FIELDS}
    used_columns: set = set()
    for score, field, col in candidates:
        if mapping[field] is None and col not in used_columns:
            mapping[field] = col
            used_columns.add(col)

    return mapping


def missing_required(mapping: Dict[str, Optional[str]]) -> List[str]:
    """Devuelve los campos imprescindibles que no se han podido mapear."""
    return [f for f in REQUIRED_FIELDS if mapping.get(f) is None]
