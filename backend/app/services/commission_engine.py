"""Motor de calculo de comisiones.

Recibe filas normalizadas y configuracion, y produce un resultado por comercial,
el resultado de la pareja Eva-Sara y una lista de incidencias/alertas.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from app.data.tables import (
    determinar_nivel_pareja,
    lookup_rappel_bonus_general,
    lookup_rappel_individual,
    lookup_super_concurso_pareja,
    nivel_pareja_index,
)
from app.models.schemas import ComercialResult, Incidencia, ParejaResult
from app.services.validators import (
    adw_punto_fila,
    clasificar_fila,
    fila_incluida,
    rns_punto_fila,
)
from app.utils.normalize import names_match, normalize_text


def _aplicar_alias_comerciales(
    rows: List[Dict[str, Any]], config: Dict[str, Any]
) -> None:
    """Sustituye el nombre de la comercial por su alias canonico (in place).

    Permite que 'HinestrosaBea' (tal cual viene en el Excel) se trate como
    'Bea'. La comparacion ignora mayusculas y tildes.
    """
    alias = config.get("alias_comerciales") or {}
    if not alias:
        return
    norm_map = {normalize_text(k): v for k, v in alias.items()}
    for row in rows:
        comercial = row.get("comercial")
        if comercial is None:
            continue
        canonico = norm_map.get(normalize_text(comercial))
        if canonico:
            row["comercial"] = canonico


def _agrupar_por_comercial(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa las filas por nombre de comercial normalizado, conservando orden."""
    grupos: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        comercial = row.get("comercial")
        if comercial is None or normalize_text(comercial) == "":
            continue
        key = normalize_text(comercial)
        grupos.setdefault(key, []).append(row)
    return grupos


def _es_pareja(nombre: str, config: Dict[str, Any]) -> bool:
    pareja = config.get("pareja_fija", ["Eva", "Sara"])
    return any(names_match(nombre, p) for p in pareja)


def _filtrar_comerciales(
    rows: List[Dict[str, Any]], config: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Incidencia]]:
    """Conserva solo las ventas de las comerciales validas configuradas."""
    validas = config.get("comerciales_validas") or []
    if not validas:
        return rows, []
    norm_validas = {normalize_text(v) for v in validas}
    incluidas: List[Dict[str, Any]] = []
    ignoradas: Dict[str, str] = {}
    for row in rows:
        comercial = row.get("comercial")
        if comercial is None or normalize_text(comercial) == "":
            incluidas.append(row)  # las filas sin comercial se gestionan aparte
            continue
        if normalize_text(comercial) in norm_validas:
            incluidas.append(row)
        else:
            ignoradas[normalize_text(comercial)] = comercial
    incidencias: List[Incidencia] = []
    if ignoradas:
        nombres = sorted(set(ignoradas.values()))
        incidencias.append(
            Incidencia(
                tipo="comercial_fuera_de_lista",
                descripcion=(
                    "Se ignoraron ventas de comerciales fuera de la lista de "
                    f"revision: {', '.join(nombres)}."
                ),
                gravedad="baja",
            )
        )
    return incluidas, incidencias


def _filtrar_filas_incluidas(
    rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    """Conserva solo las filas que pasan el filtro de pizarra/categoria."""
    incluidas = [r for r in rows if fila_incluida(r)]
    excluidas = len(rows) - len(incluidas)
    return incluidas, excluidas


def calcular_porcentaje_concurso(
    pizarra_1_final: float,
    pizarra_2_ajustada: float,
    config: Dict[str, Any],
) -> float:
    """Calcula el porcentaje de concurso mensual individual (0..100).

    El objetivo es el TOTAL de ventas: Pizarra 1 + Pizarra 2 ajustada debe
    llegar al minimo (objetivo_pizarra_1 + objetivo_pizarra_2 = 25). Mezclar
    categorias (frias de Pizarra 1 y upselling de Pizarra 2) hacia ese total ya
    sirve de compensacion. Ejemplo: Virginia 8 + 17 = 25 -> 100%.

    El resultado se redondea al entero mas cercano (>= 0,5 sube, < 0,5 baja).
    Un valor proximo (p.ej. 99,6%) se redondea a 99% para no fabricar un 100%
    que no se ha alcanzado realmente.
    """
    obj1 = max(0, int(config.get("objetivo_pizarra_1", 13)))
    obj2 = max(0, int(config.get("objetivo_pizarra_2", 12)))
    objetivo_total = max(1, obj1 + obj2)
    total = pizarra_1_final + pizarra_2_ajustada
    # Alcanzado el minimo de ventas -> 100%.
    if total >= objetivo_total:
        return 100.0
    # Redondeo "round half up" al entero.
    entero = math.floor(total / objetivo_total * 100.0 + 0.5)
    # No se ha alcanzado el minimo: nunca mostrar 100%.
    if entero >= 100:
        entero = 99
    return float(entero)


def _importe_concurso_equipo(nombre: str, config: Dict[str, Any]) -> float:
    """Devuelve el importe de concurso del equipo al que pertenece la comercial.

    Si no esta en ningun equipo, usa ``importe_concurso_mensual`` como respaldo.
    """
    equipos = (
        (config.get("equipo_1") or [], config.get("importe_concurso_equipo_1", 0.0)),
        (config.get("equipo_2") or [], config.get("importe_concurso_equipo_2", 0.0)),
    )
    for miembros, importe in equipos:
        if any(names_match(nombre, m) for m in miembros):
            return float(importe or 0.0)
    return float(config.get("importe_concurso_mensual", 0.0) or 0.0)


def procesar_comercial(
    nombre: str,
    filas: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> ComercialResult:
    """Procesa todas las ventas de una comercial y calcula sus magnitudes."""
    res = ComercialResult(comercial=nombre)

    adw_bloque = int(config.get("adw_bloque_para_punto", 3))
    rns_bloque = int(config.get("rns_bloque_para_punto", 4))

    acum_adw = 0
    acum_rns = 0
    ventas_computables = 0.0
    pizarra_1_real = 0.0
    pizarra_2_real = 0.0
    adw_computables = 0
    rns_computables = 0
    ventas_nuevas_499 = 0
    frias_computables = 0.0
    upselling_computable = 0.0
    comision_declarada_total: Optional[float] = None

    filas_detalle: List[Dict[str, Any]] = []

    for row in filas:
        clasif = clasificar_fila(row, config)
        valor = clasif["valor_computable"]
        alertas_fila: List[str] = []

        if clasif["es_venta_859"]:
            alertas_fila.append("Venta 859 computada como doble (2).")
        if clasif["incluida"] and not clasif["computa"]:
            alertas_fila.append("Movimiento de precio: se revisa pero no computa.")

        # Acumular ADW / RNS y calcular punto en esta fila.
        punto_adw = 0
        punto_rns = 0
        if clasif["es_adw"]:
            acum_adw += valor
            adw_computables += valor
            # La cartera ES una venta de Pizarra 2: cuenta como tal y, ademas,
            # suma un punto ADW por cada bloque (3 por defecto).
            pizarra_2_real += valor
            # El punto se evalua tras cada incremento; puede generar varios
            # puntos si una venta doble cruza un hito.
            punto_adw = _puntos_en_incremento(acum_adw, valor, adw_bloque)
        elif clasif["es_rns"]:
            acum_rns += valor
            rns_computables += valor
            punto_rns = _puntos_en_incremento(acum_rns, valor, rns_bloque)
        else:
            # Venta normal: cuenta para su pizarra.
            if clasif["es_pizarra_1"]:
                pizarra_1_real += valor
            elif clasif["es_pizarra_2"]:
                pizarra_2_real += valor

        # Las ventas computables totales incluyen todo lo que aporta valor.
        ventas_computables += valor

        if clasif["es_venta_nueva_499"]:
            ventas_nuevas_499 += 1
        if clasif["es_venta_fria"]:
            frias_computables += valor
        if clasif["es_upselling"]:
            upselling_computable += valor

        # Comision declarada: se acumula si existe.
        cd = row.get("comision_declarada")
        if cd is not None:
            comision_declarada_total = (comision_declarada_total or 0.0) + cd

        fila_detalle = {
            "Fecha": row.get("fecha_venta"),
            "Comercial": row.get("comercial"),
            "Cliente": row.get("cliente"),
            "Tipo venta original": row.get("tipo_venta"),
            "Tipo venta normalizado": clasif["tipo_venta_normalizado"],
            "Servicio contratado": row.get("servicio_contratado"),
            "Pizarra original": row.get("pizarra"),
            "Pizarra normalizada": clasif["pizarra_normalizada"],
            "Importe": row.get("importe_venta"),
            "Es venta 859": clasif["es_venta_859"],
            "Valor computable": valor,
            "Computa": clasif["computa"],
            "Es Pizarra 1": clasif["es_pizarra_1"],
            "Es Pizarra 2": clasif["es_pizarra_2"],
            "Es cartera (ADW)": clasif["es_cartera"],
            "Numero acumulado ADW": acum_adw if clasif["es_adw"] else "",
            "Punto ADW en esta fila": punto_adw,
            "Es subida precio RNS": clasif["es_rns"],
            "Numero acumulado RNS": acum_rns if clasif["es_rns"] else "",
            "Punto RNS en esta fila": punto_rns,
            "Es igual de precio": clasif["es_igual_precio"],
            "Es bajada de precio": clasif["es_bajada_precio"],
            "Es upselling": clasif["es_upselling"],
            "Es venta fria": clasif["es_venta_fria"],
            "Es venta nueva 499+": clasif["es_venta_nueva_499"],
            "Comision declarada": cd,
            "Observaciones": row.get("observaciones"),
            "Alertas fila": "; ".join(alertas_fila),
        }
        filas_detalle.append(fila_detalle)

    # Puntos totales = ventas / bloque, redondeado al entero mas cercano
    # (>= 0,5 sube): p.ej. 27 RNS / 4 = 6,75 -> 7 puntos.
    puntos_adw = math.floor(adw_computables / adw_bloque + 0.5) if adw_bloque > 0 else 0
    puntos_rns = math.floor(rns_computables / rns_bloque + 0.5) if rns_bloque > 0 else 0

    pizarra_2_ajustada = pizarra_2_real + puntos_adw + puntos_rns
    porcentaje = calcular_porcentaje_concurso(pizarra_1_real, pizarra_2_ajustada, config)
    importe_concurso = round(
        porcentaje / 100.0 * _importe_concurso_equipo(nombre, config), 2
    )

    # Equivalencias entre ventas.
    equiv = float(config.get("equivalencia_upselling_a_fria", 0.5))
    upselling_equiv_fria = upselling_computable * equiv
    ventas_equivalentes_totales = frias_computables + upselling_equiv_fria

    # Ventas computables totales = Pizarra 1 + Pizarra 2 ajustada. Las ventas
    # de cartera (ADW) y de subida de precio (RNS) ya se reflejan en la Pizarra
    # 2 ajustada (como puntos), por lo que no se cuentan ademas en bruto.
    ventas_computables = pizarra_1_real + pizarra_2_ajustada

    # Rellenar resultado.
    res.ventas_computables_totales = ventas_computables
    res.pizarra_1_final = pizarra_1_real
    res.pizarra_2_real = pizarra_2_real
    res.adw_computables = adw_computables
    res.puntos_adw = puntos_adw
    res.rns_computables = rns_computables
    res.puntos_rns = puntos_rns
    res.pizarra_2_ajustada = pizarra_2_ajustada
    res.porcentaje_concurso = porcentaje
    res.importe_concurso_obtenido = importe_concurso
    res.ventas_nuevas_499 = ventas_nuevas_499
    res.ventas_frias_computables = frias_computables
    res.upselling_computable = upselling_computable
    res.upselling_equivalente_fria = round(upselling_equiv_fria, 2)
    res.ventas_equivalentes_totales = round(ventas_equivalentes_totales, 2)
    res.comision_declarada = comision_declarada_total
    res.filas = filas_detalle
    res.mes_consecutivo_individual = _mes_consecutivo_individual(nombre, config)

    return res


def _puntos_en_incremento(acumulado: int, incremento: int, bloque: int) -> int:
    """Cuenta cuantos multiplos del bloque se cruzan al sumar el incremento.

    Para una venta normal (incremento 1) devuelve 0 o 1; para una venta doble
    (incremento 2) puede devolver hasta 1 punto adicional si cruza un hito.
    """
    if bloque <= 0 or incremento <= 0:
        return 0
    antes = (acumulado - incremento) // bloque
    despues = acumulado // bloque
    return despues - antes


def _mes_consecutivo_individual(nombre: str, config: Dict[str, Any]) -> Any:
    """Obtiene el mes consecutivo individual informado para la comercial."""
    mapa = config.get("meses_consecutivos_individual", {}) or {}
    key = normalize_text(nombre)
    for k, v in mapa.items():
        if normalize_text(k) == key:
            return v
    return None


def aplicar_premios(
    res: ComercialResult, config: Dict[str, Any]
) -> List[Incidencia]:
    """Aplica premios adicionales (499+, rappel bonus, rappel individual).

    El super concurso de pareja se aplica aparte. Devuelve incidencias generadas.
    """
    incidencias: List[Incidencia] = []
    solo_si_100 = config.get("aplicar_premios_solo_si_100_concurso", True)
    cumple_100 = res.porcentaje_concurso >= 100

    obligatorias = int(config.get("ventas_obligatorias_individual", 25))
    ventas_validas = max(0, int(round(res.ventas_computables_totales)) - obligatorias)
    res.ventas_para_rappel_bonus = ventas_validas
    res.ventas_para_rappel_individual = ventas_validas

    # Nivel de rappel individual (se calcula siempre como informacion).
    nivel, importe_individual = lookup_rappel_individual(
        ventas_validas, res.mes_consecutivo_individual
    )
    res.nivel_rappel_individual = nivel

    # Rappel bonus general (informativo).
    importe_bonus = lookup_rappel_bonus_general(
        ventas_validas,
        permitir_extrapolar=config.get("permitir_extrapolar_rappel_bonus", False),
    )

    # Premio ventas nuevas 499+.
    minimo_499 = int(config.get("minimo_ventas_nuevas_499", 6))
    premio_499 = 0.0
    if res.ventas_nuevas_499 >= minimo_499:
        premio_499 = float(config.get("premio_ventas_nuevas_499", 225.0))

    # El rappel bonus general y el rappel individual se aplican siempre
    # (proporcionalmente a las ventas validas). Lo unico que requiere llegar al
    # 100% del concurso es el premio de ventas nuevas 499+ (225 €).
    res.rappel_bonus_general = importe_bonus
    res.rappel_individual = importe_individual

    if solo_si_100 and not cumple_100:
        res.premio_ventas_nuevas_499 = 0.0
        incidencias.append(
            Incidencia(
                comercial=res.comercial,
                tipo="concurso_menor_100",
                descripcion=(
                    f"{res.comercial}: concurso al {res.porcentaje_concurso}% (<100%). "
                    "No se aplica el premio de ventas nuevas 499+ (225 €); el resto "
                    "de importes sí se calculan."
                ),
                gravedad="media",
            )
        )
        res.alertas.append(
            "Concurso < 100%: no aplica el premio 499+ (el total sí se calcula)."
        )
    else:
        res.premio_ventas_nuevas_499 = premio_499

    if res.mes_consecutivo_individual is None and (nivel is not None):
        incidencias.append(
            Incidencia(
                comercial=res.comercial,
                tipo="mes_consecutivo_no_informado",
                descripcion=(
                    f"{res.comercial}: mes consecutivo individual no informado. "
                    "Se asume 1er mes para el rappel individual."
                ),
                gravedad="baja",
            )
        )
        res.alertas.append("Mes consecutivo individual no informado (se asume 1).")

    if premio_499 > 0 and solo_si_100 and not cumple_100:
        res.alertas.append(
            "Cumple ventas 499+ pero no llega al 100%: premio 499+ no aplicado."
        )

    return incidencias


def procesar_pareja(
    resultados: Dict[str, ComercialResult],
    config: Dict[str, Any],
) -> Tuple[Optional[ParejaResult], List[Incidencia]]:
    """Calcula el super concurso de pareja Eva + Sara una sola vez."""
    incidencias: List[Incidencia] = []
    pareja_nombres = config.get("pareja_fija", ["Eva", "Sara"])
    if len(pareja_nombres) < 2:
        return None, incidencias

    nombre_a, nombre_b = pareja_nombres[0], pareja_nombres[1]
    res_a = _buscar_resultado(resultados, nombre_a)
    res_b = _buscar_resultado(resultados, nombre_b)

    if res_a is None or res_b is None:
        # Si falta alguna de las dos, no se calcula la pareja.
        if res_a is None and res_b is None:
            return None, incidencias
        faltante = nombre_b if res_a is not None else nombre_a
        incidencias.append(
            Incidencia(
                tipo="pareja_incompleta",
                descripcion=(
                    f"Solo se encontraron ventas de una integrante de la pareja. "
                    f"Falta '{faltante}'. No se calcula super concurso de pareja."
                ),
                gravedad="media",
            )
        )
        return None, incidencias

    pr = ParejaResult()
    pr.ventas_computables_eva = res_a.ventas_computables_totales
    pr.ventas_computables_sara = res_b.ventas_computables_totales
    pr.ventas_brutas_pareja = (
        res_a.ventas_computables_totales + res_b.ventas_computables_totales
    )
    obligatorias_pareja = int(config.get("ventas_obligatorias_pareja", 50))
    pr.ventas_obligatorias_restadas = obligatorias_pareja
    pr.ventas_validas_pareja = max(0.0, pr.ventas_brutas_pareja - obligatorias_pareja)
    pr.porcentaje_concurso_eva = res_a.porcentaje_concurso
    pr.porcentaje_concurso_sara = res_b.porcentaje_concurso
    pr.autorizacion_raul = str(config.get("autorizacion_raul", "Pendiente"))
    pr.mes_consecutivo_pareja = config.get("mes_consecutivo_pareja")

    # Condicion: ambas deben llegar al 100%.
    ambas_100 = res_a.porcentaje_concurso >= 100 and res_b.porcentaje_concurso >= 100

    nivel_actual = determinar_nivel_pareja(int(round(pr.ventas_validas_pareja)))
    pr.nivel_pareja_actual = nivel_actual

    alertas: List[str] = []

    if not ambas_100:
        pr.aplica_pareja = False
        pr.premio_por_persona = 0.0
        quien = []
        if res_a.porcentaje_concurso < 100:
            quien.append(nombre_a)
        if res_b.porcentaje_concurso < 100:
            quien.append(nombre_b)
        alertas.append(
            f"No aplica super concurso pareja: {', '.join(quien)} no llega al 100%."
        )
        incidencias.append(
            Incidencia(
                tipo="pareja_sin_100",
                descripcion=(
                    f"Eva/Sara: {', '.join(quien)} no llega al 100%. "
                    "No se aplica super concurso de pareja."
                ),
                gravedad="media",
            )
        )
    elif nivel_actual is None:
        pr.aplica_pareja = False
        pr.premio_por_persona = 0.0
        alertas.append("Ventas validas de pareja insuficientes para cualquier nivel.")
    else:
        # Determinar mes consecutivo y gestionar subida de nivel.
        mes_pareja = config.get("mes_consecutivo_pareja")
        importe = lookup_super_concurso_pareja(nivel_actual, mes_pareja)

        nivel_anterior = config.get("nivel_pareja_mes_anterior")
        idx_actual = nivel_pareja_index(nivel_actual)
        idx_anterior = nivel_pareja_index(nivel_anterior)

        if idx_anterior >= 0 and idx_actual > idx_anterior:
            # Subida de nivel: requiere autorizacion de Raul para importe maximo.
            alerta_subida = (
                "Subida de nivel detectada en pareja. Para aplicar el importe "
                "maximo del nuevo nivel se requiere autorizacion de Raul."
            )
            alertas.append(alerta_subida)
            incidencias.append(
                Incidencia(
                    tipo="subida_nivel_pareja",
                    descripcion=alerta_subida,
                    gravedad="alta",
                )
            )
            if normalize_text(pr.autorizacion_raul) != "si":
                # No aplicar importe maximo: usar el importe del nivel anterior.
                importe = lookup_super_concurso_pareja(nivel_anterior, mes_pareja)
                pr.nivel_pareja_actual = nivel_anterior
                alertas.append(
                    "Autorizacion de Raul no concedida: se aplica importe del nivel anterior."
                )

        if mes_pareja is None:
            alertas.append("Mes consecutivo de pareja no informado (se asume 1).")
            incidencias.append(
                Incidencia(
                    tipo="mes_consecutivo_pareja_no_informado",
                    descripcion="Mes consecutivo de pareja no informado. Se asume 1er mes.",
                    gravedad="baja",
                )
            )

        pr.aplica_pareja = importe > 0
        pr.premio_por_persona = importe

    pr.importe_final_eva = pr.premio_por_persona
    pr.importe_final_sara = pr.premio_por_persona
    pr.alerta = "; ".join(alertas) if alertas else None

    # Volcar el premio en cada integrante.
    res_a.super_concurso_pareja = pr.premio_por_persona
    res_b.super_concurso_pareja = pr.premio_por_persona
    if pr.premio_por_persona > 0:
        res_a.alertas.append(f"Super concurso pareja aplicado: {pr.premio_por_persona} €.")
        res_b.alertas.append(f"Super concurso pareja aplicado: {pr.premio_por_persona} €.")

    return pr, incidencias


def _buscar_resultado(
    resultados: Dict[str, ComercialResult], nombre: str
) -> Optional[ComercialResult]:
    key = normalize_text(nombre)
    for k, v in resultados.items():
        if k == key or names_match(v.comercial, nombre):
            return v
    return None


def finalizar_comercial(res: ComercialResult, config: Dict[str, Any]) -> None:
    """Calcula total_final, diferencia y estado frente a comision declarada."""
    es_pareja = _es_pareja(res.comercial, config)
    if not es_pareja:
        # Resto de comerciales: no hay super concurso de pareja; se suman
        # rappel bonus general + rappel individual.
        res.super_concurso_pareja = 0.0
    else:
        # Eva y Sara: el rappel en pareja sustituye al rappel individual.
        # Conservan concurso, premio 499+ y rappel bonus general.
        if res.rappel_individual:
            res.alertas.append(
                "Rappel individual sustituido por el super concurso de pareja."
            )
        res.rappel_individual = 0.0

    res.total_final = round(
        res.importe_concurso_obtenido
        + res.premio_ventas_nuevas_499
        + res.rappel_bonus_general
        + res.rappel_individual
        + res.super_concurso_pareja,
        2,
    )

    if res.comision_declarada is None:
        res.diferencia = None
        res.estado = "No comprobable"
    else:
        diferencia = round(res.comision_declarada - res.total_final, 2)
        res.diferencia = diferencia
        if abs(diferencia) < 0.01:
            res.estado = "Correcta"
        elif diferencia > 0:
            res.estado = "Declarada de mas"
            res.alertas.append(
                f"Comision declarada de mas: {diferencia} € sobre lo esperado."
            )
        else:
            res.estado = "Declarada de menos"
            res.alertas.append(
                f"Comision declarada de menos: {abs(diferencia)} € por debajo."
            )


def analizar(
    rows: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[Dict[str, ComercialResult], Optional[ParejaResult], List[Incidencia]]:
    """Orquesta el calculo completo a partir de las filas normalizadas."""
    incidencias: List[Incidencia] = []

    # 0) Normalizar nombres por alias (p.ej. 'HinestrosaBea' -> 'Bea').
    _aplicar_alias_comerciales(rows, config)

    # 1) Conservar solo las comerciales validas.
    rows, inc_comerciales = _filtrar_comerciales(rows, config)
    incidencias.extend(inc_comerciales)

    # 2) Conservar solo las filas revisables (pizarra 1/2, subida/igual/bajada
    #    de precio, o categoria 'cartera').
    rows, n_excluidas = _filtrar_filas_incluidas(rows)
    if n_excluidas > 0:
        incidencias.append(
            Incidencia(
                tipo="filas_fuera_de_filtro",
                descripcion=(
                    f"Se descartaron {n_excluidas} fila(s) que no cumplen el "
                    "filtro de revision (pizarra 1/2, subida/igual/bajada de "
                    "precio o categoria 'cartera')."
                ),
                gravedad="baja",
            )
        )

    grupos = _agrupar_por_comercial(rows)

    if not grupos:
        incidencias.append(
            Incidencia(
                tipo="sin_ventas",
                descripcion="No se encontraron ventas con comercial asignada.",
                gravedad="alta",
            )
        )
        return {}, None, incidencias

    resultados: Dict[str, ComercialResult] = {}
    for key, filas in grupos.items():
        nombre = filas[0].get("comercial") or key
        res = procesar_comercial(nombre, filas, config)
        if res.ventas_computables_totales == 0:
            res.alertas.append("Comercial sin ventas computables.")
            incidencias.append(
                Incidencia(
                    comercial=nombre,
                    tipo="comercial_sin_ventas",
                    descripcion=f"{nombre}: sin ventas computables.",
                    gravedad="media",
                )
            )
        incidencias.extend(aplicar_premios(res, config))
        resultados[key] = res

    # Pareja Eva-Sara (debe calcularse antes de finalizar para volcar el premio).
    pareja, inc_pareja = procesar_pareja(resultados, config)
    incidencias.extend(inc_pareja)

    # Finalizar totales y diferencias.
    for res in resultados.values():
        finalizar_comercial(res, config)

    return resultados, pareja, incidencias
