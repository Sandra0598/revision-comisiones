"""Configuracion por defecto editable del sistema de comisiones.

Todos los valores aqui definidos pueden ser sobreescritos por el JSON que el
frontend envia en ``POST /api/analyze``. El endpoint ``GET /api/config/defaults``
devuelve exactamente este diccionario.
"""

from __future__ import annotations

from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    # Importe total del concurso mensual por equipo. El concurso de cada
    # comercial es su % de concurso aplicado al importe de SU equipo.
    "importe_concurso_equipo_1": 0.0,
    "importe_concurso_equipo_2": 0.0,
    # Composicion de los equipos del concurso.
    "equipo_1": ["Sara", "Eva", "Virginia", "Isamar"],
    "equipo_2": ["Bea", "Laura", "Susana", "Estela"],
    # Importe de concurso por defecto para comerciales sin equipo asignado.
    "importe_concurso_mensual": 0.0,
    # Premio por ventas nuevas de 499 o mas.
    "premio_ventas_nuevas_499": 225.0,
    "minimo_ventas_nuevas_499": 6,
    # Ventas obligatorias antes de consultar tablas de rappel.
    "ventas_obligatorias_individual": 25,
    "ventas_obligatorias_pareja": 50,
    # Objetivos de las pizarras.
    "objetivo_pizarra_1": 13,
    "objetivo_pizarra_2": 12,
    # Referencias de equivalencia entre ventas frias y upselling.
    "referencia_frias_100": 13,
    "referencia_upselling_100": 7,
    "equivalencia_upselling_a_fria": 0.5,
    # Hitos de puntos para Pizarra 2.
    "adw_bloque_para_punto": 3,
    "rns_bloque_para_punto": 4,
    # Venta doble: importes que cuentan como 2 ventas (759 € y 859 €).
    "importes_venta_doble": [759.0, 859.0],
    "importe_venta_doble": 859.0,  # legado (retrocompatibilidad)
    "activar_venta_doble_859": True,
    # Premios adicionales solo si se llega al 100% del concurso.
    "aplicar_premios_solo_si_100_concurso": True,
    # Modalidad de calculo del porcentaje de concurso.
    "modalidad_porcentaje_concurso": "pizarra_1_y_pizarra_2",
    # Comerciales a revisar. Las ventas de cualquier otra persona se ignoran.
    "comerciales_validas": [
        "Eva", "Laura", "Estela", "Bea", "Isamar", "Sara", "Susana", "Virginia",
    ],
    # Alias: nombre tal cual aparece en el Excel -> nombre canonico a usar.
    # (las mayusculas/tildes ya se ignoran; esto es para nombres distintos).
    "alias_comerciales": {
        "HinestrosaBea": "Bea",
    },
    # Pareja fija del super concurso.
    "pareja_fija": ["Eva", "Sara"],
    # Autorizacion de Raul para aplicar importe maximo al subir de nivel.
    # Valores admitidos: "Si", "No", "Pendiente".
    "autorizacion_raul": "Pendiente",
    # Si se permite extrapolar la tabla de rappel bonus mas alla del ultimo tramo.
    "permitir_extrapolar_rappel_bonus": False,
}


def get_default_config() -> Dict[str, Any]:
    """Devuelve una copia mutable de la configuracion por defecto."""
    import copy

    return copy.deepcopy(DEFAULT_CONFIG)


def merge_config(overrides: Dict[str, Any] | None) -> Dict[str, Any]:
    """Combina la configuracion por defecto con los valores recibidos."""
    config = get_default_config()
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                config[key] = value
    return config
