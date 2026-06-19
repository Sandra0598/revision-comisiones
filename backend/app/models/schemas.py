"""Modelos pydantic para configuracion, filas, resultados e incidencias."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

class CommissionConfig(BaseModel):
    """Configuracion editable del sistema de comisiones.

    Todos los campos tienen valor por defecto para que el frontend pueda enviar
    solo aquellos que desea sobreescribir.
    """

    importe_concurso_mensual: float = 0.0
    premio_ventas_nuevas_499: float = 225.0
    minimo_ventas_nuevas_499: int = 6
    ventas_obligatorias_individual: int = 25
    ventas_obligatorias_pareja: int = 50
    objetivo_pizarra_1: int = 13
    objetivo_pizarra_2: int = 12
    referencia_frias_100: int = 13
    referencia_upselling_100: int = 7
    equivalencia_upselling_a_fria: float = 0.5
    adw_bloque_para_punto: int = 3
    rns_bloque_para_punto: int = 4
    importe_venta_doble: float = 859.0
    activar_venta_doble_859: bool = True
    aplicar_premios_solo_si_100_concurso: bool = True
    modalidad_porcentaje_concurso: str = "pizarra_1_y_pizarra_2"
    comerciales_validas: List[str] = Field(
        default_factory=lambda: [
            "Eva", "Laura", "Estela", "Bea", "Isamar", "Sara", "Susana", "Virginia",
        ]
    )
    pareja_fija: List[str] = Field(default_factory=lambda: ["Eva", "Sara"])
    autorizacion_raul: str = "Pendiente"
    permitir_extrapolar_rappel_bonus: bool = False

    # Datos auxiliares que el frontend puede enviar por comercial.
    # Mapea nombre normalizado -> mes consecutivo individual.
    meses_consecutivos_individual: Dict[str, Any] = Field(default_factory=dict)
    # Datos de consecutividad de la pareja.
    mes_consecutivo_pareja: Optional[Any] = None
    nivel_pareja_mes_anterior: Optional[str] = None
    nivel_pareja_actual: Optional[str] = None
    # Mes/anio de revision (si no se pasa se infiere del Excel).
    mes_revision: Optional[int] = None
    anio_revision: Optional[int] = None


# ---------------------------------------------------------------------------
# Incidencias
# ---------------------------------------------------------------------------

class Incidencia(BaseModel):
    """Una incidencia o alerta detectada durante el analisis."""

    fila_original: Optional[int] = None
    comercial: Optional[str] = None
    tipo: str
    descripcion: str
    gravedad: str = "media"  # baja | media | alta


# ---------------------------------------------------------------------------
# Resultado por comercial
# ---------------------------------------------------------------------------

class ComercialResult(BaseModel):
    """Resultado calculado para una comercial."""

    comercial: str
    ventas_computables_totales: float = 0.0
    pizarra_1_final: float = 0.0
    pizarra_2_real: float = 0.0
    adw_computables: int = 0
    puntos_adw: int = 0
    rns_computables: int = 0
    puntos_rns: int = 0
    pizarra_2_ajustada: float = 0.0
    porcentaje_concurso: float = 0.0
    importe_concurso_obtenido: float = 0.0

    ventas_nuevas_499: int = 0
    premio_ventas_nuevas_499: float = 0.0

    ventas_para_rappel_bonus: int = 0
    rappel_bonus_general: float = 0.0

    ventas_para_rappel_individual: int = 0
    nivel_rappel_individual: Optional[str] = None
    mes_consecutivo_individual: Optional[Any] = None
    rappel_individual: float = 0.0

    super_concurso_pareja: float = 0.0

    # Datos auxiliares de equivalencia.
    ventas_frias_computables: float = 0.0
    upselling_computable: float = 0.0
    upselling_equivalente_fria: float = 0.0
    ventas_equivalentes_totales: float = 0.0

    total_final: float = 0.0
    comision_declarada: Optional[float] = None
    diferencia: Optional[float] = None
    estado: str = "No comprobable"
    alertas: List[str] = Field(default_factory=list)

    # Filas detalladas (cada fila es un dict con las columnas auxiliares).
    filas: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Resultado de la pareja
# ---------------------------------------------------------------------------

class ParejaResult(BaseModel):
    ventas_computables_eva: float = 0.0
    ventas_computables_sara: float = 0.0
    ventas_brutas_pareja: float = 0.0
    ventas_obligatorias_restadas: int = 50
    ventas_validas_pareja: float = 0.0
    porcentaje_concurso_eva: float = 0.0
    porcentaje_concurso_sara: float = 0.0
    aplica_pareja: bool = False
    nivel_pareja_actual: Optional[str] = None
    mes_consecutivo_pareja: Optional[Any] = None
    premio_por_persona: float = 0.0
    autorizacion_raul: str = "Pendiente"
    alerta: Optional[str] = None
    importe_final_eva: float = 0.0
    importe_final_sara: float = 0.0


# ---------------------------------------------------------------------------
# Respuesta del analisis
# ---------------------------------------------------------------------------

class AnalyzeResponse(BaseModel):
    """Respuesta de POST /api/analyze."""

    mes_revision: int
    anio_revision: int
    nombre_archivo: str
    config_usada: Dict[str, Any]
    resumen: List[Dict[str, Any]]
    pareja: Optional[ParejaResult] = None
    incidencias: List[Incidencia] = Field(default_factory=list)
    total_comerciales: int = 0
    total_ventas_procesadas: int = 0
