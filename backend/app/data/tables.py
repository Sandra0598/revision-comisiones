"""Tablas de rappel y super concurso, mas las funciones de consulta.

Estas tablas son los importes oficiales. Las funciones de consulta encapsulan la
logica de "buscar el tramo correcto" para que el motor de comisiones no tenga que
conocer la estructura interna de cada tabla.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Rappel de bonus general (por ventas por encima de las 25 obligatorias)
# ---------------------------------------------------------------------------
# Clave: numero de ventas validas para rappel (ventas_computables - 25).
# Valor: importe del bonus. Aplica a partir de 8.
RAPPEL_BONUS_GENERAL: Dict[int, float] = {
    8: 40, 9: 40, 10: 60, 11: 60, 12: 80, 13: 80, 14: 100, 15: 100, 16: 100,
    17: 120, 18: 127, 19: 134, 20: 141, 21: 148, 22: 155, 23: 162, 24: 169,
    25: 176, 26: 183, 27: 190, 28: 197, 29: 204, 30: 211, 31: 218, 32: 225,
    33: 232, 34: 239, 35: 246, 36: 253, 37: 260, 38: 267, 39: 274, 40: 277,
    41: 280, 42: 283, 43: 286, 44: 289, 45: 292, 46: 295, 47: 298, 48: 301,
    49: 304, 50: 307, 51: 310, 52: 313, 53: 316, 54: 319, 55: 322, 56: 325,
    57: 328, 58: 331,
}

_RAPPEL_BONUS_MIN = 8
_RAPPEL_BONUS_MAX = 58


def lookup_rappel_bonus_general(
    ventas_validas: int, permitir_extrapolar: bool = False
) -> float:
    """Devuelve el importe del rappel bonus general.

    - Menos de 8 ventas validas -> 0.
    - Mas de 58 -> ultimo tramo (331) salvo que se permita extrapolar.
    """
    if ventas_validas < _RAPPEL_BONUS_MIN:
        return 0.0
    if ventas_validas in RAPPEL_BONUS_GENERAL:
        return float(RAPPEL_BONUS_GENERAL[ventas_validas])
    if ventas_validas > _RAPPEL_BONUS_MAX:
        if permitir_extrapolar:
            # Extrapolacion lineal con la pendiente del ultimo tramo (+3).
            extra = ventas_validas - _RAPPEL_BONUS_MAX
            return float(RAPPEL_BONUS_GENERAL[_RAPPEL_BONUS_MAX] + 3 * extra)
        return float(RAPPEL_BONUS_GENERAL[_RAPPEL_BONUS_MAX])
    # Por seguridad, buscar el tramo inferior mas cercano.
    candidatos = [k for k in RAPPEL_BONUS_GENERAL if k <= ventas_validas]
    if candidatos:
        return float(RAPPEL_BONUS_GENERAL[max(candidatos)])
    return 0.0


# ---------------------------------------------------------------------------
# Rappel individual solitario
# ---------------------------------------------------------------------------
# Cada nivel define las ventas necesarias (sobre ventas_para_rappel_individual,
# es decir ya restadas las 25) y el importe segun el mes consecutivo.
# Estructura: nivel -> {"ventas": int, "1": float, "2": float, "3": float, "siguientes": float}
RAPPEL_INDIVIDUAL: List[Tuple[str, Dict[str, float]]] = [
    ("baby",   {"ventas": 21, "1": 75,  "2": 125, "3": 175,  "siguientes": 175}),
    ("junior", {"ventas": 27, "1": 150, "2": 250, "3": 350,  "siguientes": 350}),
    ("senior", {"ventas": 31, "1": 425, "2": 500, "3": 575,  "siguientes": 575}),
    ("1.0",    {"ventas": 35, "1": 0,   "2": 0,   "3": 640,  "siguientes": 640}),
    ("2.0",    {"ventas": 39, "1": 0,   "2": 0,   "3": 700,  "siguientes": 700}),
    ("2.5",    {"ventas": 45, "1": 0,   "2": 0,   "3": 780,  "siguientes": 780}),
    ("3.0",    {"ventas": 50, "1": 0,   "2": 0,   "3": 835,  "siguientes": 835}),
    ("3.5",    {"ventas": 56, "1": 0,   "2": 0,   "3": 915,  "siguientes": 915}),
    ("4.0",    {"ventas": 64, "1": 0,   "2": 0,   "3": 1000, "siguientes": 1000}),
]


def _normalize_mes_consecutivo(mes: object) -> str:
    """Normaliza el mes consecutivo a una de las claves '1','2','3','siguientes'."""
    if mes is None:
        return "1"
    texto = str(mes).strip().lower()
    if texto in ("1", "1.0", "primero", "primer"):
        return "1"
    if texto in ("2", "2.0", "segundo"):
        return "2"
    if texto in ("3", "3.0", "tercero", "tercer"):
        return "3"
    if texto in ("4", "siguientes", "siguiente", "mas", "+"):
        return "siguientes"
    try:
        n = int(float(texto))
        if n <= 1:
            return "1"
        if n == 2:
            return "2"
        if n == 3:
            return "3"
        return "siguientes"
    except (ValueError, TypeError):
        return "1"


def lookup_rappel_individual(
    ventas_validas: int, mes_consecutivo: object
) -> Tuple[Optional[str], float]:
    """Devuelve (nivel_alcanzado, importe) para el rappel individual.

    Elige siempre el nivel mas alto posible segun las ventas validas (ya
    restadas las 25 obligatorias).
    """
    mes_key = _normalize_mes_consecutivo(mes_consecutivo)
    nivel_alcanzado: Optional[str] = None
    importe = 0.0
    for nombre, datos in RAPPEL_INDIVIDUAL:
        if ventas_validas >= datos["ventas"]:
            nivel_alcanzado = nombre
            importe = float(datos[mes_key])
    return nivel_alcanzado, importe


# ---------------------------------------------------------------------------
# Super concurso en pareja Eva + Sara
# ---------------------------------------------------------------------------
# Umbrales "X o mas" (inclusivos) sobre ventas_validas_pareja (ya restadas las
# 50). Importe es POR PERSONA. Ej.: 63 ventas validas -> Senior.
SUPER_CONCURSO_PAREJA: List[Tuple[str, Dict[str, float]]] = [
    ("Senior", {"min_inclusivo": 63, "1": 425, "2": 500, "3": 575, "siguientes": 575}),
    ("Junior", {"min_inclusivo": 55, "1": 150, "2": 250, "3": 350, "siguientes": 350}),
    ("Baby",   {"min_inclusivo": 46, "1": 75,  "2": 125, "3": 175, "siguientes": 175}),
]

# Orden de niveles de menor a mayor para detectar subidas/bajadas.
NIVELES_PAREJA_ORDEN = ["Baby", "Junior", "Senior"]


def determinar_nivel_pareja(ventas_validas_pareja: int) -> Optional[str]:
    """Devuelve el nivel de pareja segun prioridad Senior > Junior > Baby.

    Umbrales inclusivos: alcanzar exactamente el minimo ya da ese nivel
    (p.ej. 63 -> Senior).
    """
    for nombre, datos in SUPER_CONCURSO_PAREJA:
        if ventas_validas_pareja >= datos["min_inclusivo"]:
            return nombre
    return None


def lookup_super_concurso_pareja(
    nivel: Optional[str], mes_consecutivo: object
) -> float:
    """Devuelve el importe POR PERSONA del super concurso para un nivel y mes."""
    if not nivel:
        return 0.0
    mes_key = _normalize_mes_consecutivo(mes_consecutivo)
    for nombre, datos in SUPER_CONCURSO_PAREJA:
        if nombre == nivel:
            return float(datos[mes_key])
    return 0.0


def nivel_pareja_index(nivel: Optional[str]) -> int:
    """Indice ordinal del nivel de pareja (-1 si no aplica)."""
    if not nivel:
        return -1
    try:
        return NIVELES_PAREJA_ORDEN.index(nivel)
    except ValueError:
        return -1
