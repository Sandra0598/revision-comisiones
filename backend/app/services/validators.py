"""Clasificacion de filas y validaciones testeables.

Estas funciones son puras y se prueban de forma aislada. El motor de comisiones
las usa para enriquecer cada fila con flags y puntos.
"""

from __future__ import annotations

from typing import Any, Dict

from app.utils.normalize import (
    amounts_equal,
    detect_movimiento_precio,
    detect_pizarra,
    is_upselling,
    is_venta_fria,
    normalize_text,
    servicio_es_cartera,
)


def valor_computable(importe: float | None, config: Dict[str, Any]) -> int:
    """Valor computable de una venta: 2 si es venta doble 859, 1 en otro caso."""
    if not config.get("activar_venta_doble_859", True):
        return 1
    if importe is None:
        return 1
    if amounts_equal(importe, float(config.get("importe_venta_doble", 859.0))):
        return 2
    return 1


def es_venta_doble(importe: float | None, config: Dict[str, Any]) -> bool:
    """Indica si una venta es la venta doble de 859."""
    if not config.get("activar_venta_doble_859", True):
        return False
    if importe is None:
        return False
    return amounts_equal(importe, float(config.get("importe_venta_doble", 859.0)))


def adw_punto_fila(numero_acumulado_adw: int, bloque: int = 3) -> int:
    """Devuelve 1 si el acumulado de ADW es multiplo del bloque (3 por defecto)."""
    if numero_acumulado_adw <= 0 or bloque <= 0:
        return 0
    return 1 if numero_acumulado_adw % bloque == 0 else 0


def rns_punto_fila(numero_acumulado_rns: int, bloque: int = 4) -> int:
    """Devuelve 1 si el acumulado de RNS es multiplo del bloque (4 por defecto)."""
    if numero_acumulado_rns <= 0 or bloque <= 0:
        return 0
    return 1 if numero_acumulado_rns % bloque == 0 else 0


def fila_incluida(row: Dict[str, Any]) -> bool:
    """Indica si la fila debe revisarse segun el filtro de pizarra.

    Se revisan las filas cuya columna pizarra sea 1, 2, 'Subida precio',
    'Igual de precio' o 'Bajada precio'. Las carteras son un subconjunto de
    Pizarra 2 (servicio contratado que empieza por '(m)'), por lo que ya quedan
    incluidas por su pizarra.
    """
    pizarra_raw = row.get("pizarra")
    pnum = detect_pizarra(pizarra_raw)
    movimiento = detect_movimiento_precio(pizarra_raw)
    return bool(pnum in (1, 2) or movimiento is not None)


def clasificar_fila(row: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Clasifica una fila incluida y calcula su valor computable.

    Reglas de este negocio:
      - pizarra 1 / 2            -> venta de Pizarra 1 / 2 (computa).
      - pizarra 'Subida precio'  -> subida RNS: puntos a Pizarra 2 cada 4 (computa).
      - categoria 'cartera'      -> ADW: puntos a Pizarra 2 cada 3 (computa).
      - pizarra 'Igual de precio' / 'Bajada precio' -> se muestran pero NO computan.
    Solo computan (suman a ventas, pizarras y puntos) las filas marcadas con
    ``computa``. ``valor_computable`` es 0 para las que no computan.
    """
    categoria = row.get("tipo_venta")  # columna "categoria de venta"
    producto = row.get("producto")
    servicio = row.get("servicio_contratado")  # columna "Servicio contratado"
    observaciones = row.get("observaciones")
    pizarra_raw = row.get("pizarra")
    importe = row.get("importe_venta")

    pnum = detect_pizarra(pizarra_raw)
    movimiento = detect_movimiento_precio(pizarra_raw)

    es_pizarra_1 = pnum == 1
    es_pizarra_2 = pnum == 2
    es_subida_precio = movimiento == "subida"
    es_igual_precio = movimiento == "igual"
    es_bajada_precio = movimiento == "bajada"

    # Cartera: venta de Pizarra 2 cuyo servicio contratado empieza por '(m)'.
    es_cartera = es_pizarra_2 and servicio_es_cartera(servicio)

    # ADW proviene de 'cartera'; RNS proviene de 'subida de precio'.
    es_adw = es_cartera
    es_rns = es_subida_precio

    incluida = fila_incluida(row)
    # Igual de precio y bajada de precio se muestran pero no computan.
    computa = es_pizarra_1 or es_pizarra_2 or es_subida_precio

    es_upsell = is_upselling(categoria, producto, observaciones)
    es_fria = is_venta_fria(categoria, producto, observaciones)
    # Venta nueva 499+: venta de pizarra (nueva) con importe >= 499. Las
    # carteras (mantenimientos) no se consideran ventas nuevas.
    es_nueva_499 = (
        (es_pizarra_1 or es_pizarra_2)
        and not es_cartera
        and importe is not None
        and importe >= 499
    )

    valor = valor_computable(importe, config) if computa else 0

    return {
        "tipo_venta_normalizado": normalize_text(categoria) if categoria is not None else "",
        "pizarra_normalizada": pnum,
        "incluida": incluida,
        "computa": computa,
        "es_venta_859": computa and es_venta_doble(importe, config),
        "valor_computable": valor,
        "es_pizarra_1": es_pizarra_1,
        "es_pizarra_2": es_pizarra_2,
        "es_subida_precio": es_subida_precio,
        "es_igual_precio": es_igual_precio,
        "es_bajada_precio": es_bajada_precio,
        "es_cartera": es_cartera,
        "es_adw": es_adw,
        "es_rns": es_rns,
        "es_upselling": es_upsell,
        "es_venta_fria": es_fria,
        "es_venta_nueva_499": es_nueva_499,
    }
