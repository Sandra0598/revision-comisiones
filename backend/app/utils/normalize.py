"""Funciones de normalizacion de texto, importes y clasificacion de ventas.

Todas las funciones son puras y testeables: no dependen de estado global ni de
configuracion mutable. Las reglas de deteccion (ADW, RNS, upselling, fria,
pizarras, venta nueva 499+) viven aqui para poder probarse de forma aislada.
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Optional


# ---------------------------------------------------------------------------
# Normalizacion de texto
# ---------------------------------------------------------------------------

def normalize_text(value: object) -> str:
    """Convierte a minusculas, elimina tildes y espacios sobrantes.

    >>> normalize_text("  Pizarra  Uno ")
    'pizarra uno'
    >>> normalize_text("FRÍA")
    'fria'
    """
    if value is None:
        return ""
    text = str(value)
    # Descomponer caracteres acentuados y eliminar los diacriticos.
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    # Colapsar cualquier secuencia de espacios en blanco en uno solo.
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_name(value: object) -> str:
    """Normaliza un nombre de persona para comparaciones robustas.

    Mantiene el resultado en formato titulo para mostrarlo, pero la comparacion
    debe hacerse siempre con ``normalize_text``.
    """
    norm = normalize_text(value)
    if not norm:
        return ""
    return norm.title()


def names_match(a: object, b: object) -> bool:
    """Compara dos nombres ignorando mayusculas, tildes y espacios."""
    return normalize_text(a) == normalize_text(b) and normalize_text(a) != ""


# ---------------------------------------------------------------------------
# Normalizacion de importes
# ---------------------------------------------------------------------------

def normalize_amount(value: object) -> Optional[float]:
    """Convierte importes en formatos variados a ``float``.

    Soporta '859', '859,00', '859 €', '859.00', '1.234,56', '1,234.56'.
    Devuelve ``None`` si no se puede interpretar como numero.

    >>> normalize_amount("859 €")
    859.0
    >>> normalize_amount("1.234,56")
    1234.56
    >>> normalize_amount("no es numero")
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    # Eliminar simbolos de moneda y espacios, dejando digitos y separadores.
    text = text.replace("€", "").replace("$", "").replace("EUR", "").replace("eur", "")
    text = text.replace(" ", "").strip()
    text = re.sub(r"[^0-9,.\-]", "", text)
    if text in ("", "-", ".", ","):
        return None

    has_comma = "," in text
    has_dot = "." in text

    if has_comma and has_dot:
        # El ultimo separador que aparece es el decimal.
        if text.rfind(",") > text.rfind("."):
            # Formato europeo: '1.234,56' -> miles '.', decimal ','
            text = text.replace(".", "").replace(",", ".")
        else:
            # Formato anglosajon: '1,234.56' -> miles ',', decimal '.'
            text = text.replace(",", "")
    elif has_comma:
        # Solo coma: tratarla como separador decimal.
        text = text.replace(",", ".")
    # Solo punto o sin separadores: ya es valido para float.

    try:
        return float(text)
    except ValueError:
        return None


def amounts_equal(a: Optional[float], b: float, tol: float = 0.01) -> bool:
    """Compara importes con tolerancia para evitar errores de coma flotante."""
    if a is None:
        return False
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# Deteccion de pizarras
# ---------------------------------------------------------------------------

def detect_pizarra(value: object) -> Optional[int]:
    """Detecta Pizarra 1 o Pizarra 2 a partir de texto libre.

    Reconoce 'p1', 'pizarra 1', 'Pizarra1', 'P1' -> 1
    Reconoce 'p2', 'pizarra 2', 'Pizarra2', 'P2' -> 2
    Devuelve ``None`` si no se reconoce.
    """
    norm = normalize_text(value)
    if not norm:
        return None
    # Quitar espacios internos para que 'pizarra 1' y 'pizarra1' coincidan.
    compact = norm.replace(" ", "")
    if re.search(r"(pizarra|board|equipo|p)0*1$", compact) or compact in ("1", "p1", "pizarra1"):
        return 1
    if re.search(r"(pizarra|board|equipo|p)0*2$", compact) or compact in ("2", "p2", "pizarra2"):
        return 2
    # Casos donde el numero va al final en cualquier parte.
    if compact.endswith("1") and ("pizarra" in compact or compact.startswith("p")):
        return 1
    if compact.endswith("2") and ("pizarra" in compact or compact.startswith("p")):
        return 2
    return None


# ---------------------------------------------------------------------------
# Deteccion de tipos de venta
# ---------------------------------------------------------------------------

def detect_movimiento_precio(pizarra_raw: object) -> Optional[str]:
    """Detecta el tipo de movimiento de precio desde la columna pizarra.

    Reconoce 'subida precio' -> 'subida' (subida RNS),
    'igual de precio' / 'igualada' -> 'igual',
    'bajada precio' -> 'bajada'. Devuelve None si no aplica.
    """
    p = normalize_text(pizarra_raw)
    if not p:
        return None
    # 'subida' / 'subido' / 'subir' / 'sube' precio -> subida (RNS).
    if "subid" in p or "sube" in p or "subir" in p:
        return "subida"
    if "igual" in p:
        return "igual"
    if "bajad" in p or "baja de" in p or "baja precio" in p:
        return "bajada"
    # Renovaciones/consultora etiquetadas como pizarra 3 (p.ej. '3RN.r',
    # '3Venta Consultora'): se revisan pero NO computan, igual que 'Igual de
    # precio'. Antes se descartaban en silencio por no reconocerse.
    compact = p.replace(" ", "")
    if compact.startswith("3"):
        return "igual"
    return None


def servicio_es_cartera(servicio: object) -> bool:
    """Detecta una venta de cartera por el 'Servicio contratado'.

    Son carteras (generan puntos ADW dentro de Pizarra 2) las ventas cuyo
    servicio contratado empieza por '(m)' (p.ej. '(M) Mantenimiento ...').
    """
    norm = normalize_text(servicio)
    return norm.startswith("(m")


def motivo_descarte_fila(
    estado: object, categoria: object, importe: Optional[float]
) -> Optional[str]:
    """Indica por que una fila debe descartarse por completo, o None si computa.

    Estas filas no son ventas reales y no se contabilizan para nada (ni ventas,
    ni carteras, ni comisiones). Reglas acordadas:
      - Estado 'Abono' / 'Devolucion'        -> abono.
      - Estado 'Venta no valida'             -> venta_no_valida.
      - 'Regalo' en Estado o Categoria com.  -> regalo.
      - Estado 'Baja' con importe 0 o vacio  -> baja_sin_importe (las bajas con
        importe > 0 si cuentan).
    """
    e = normalize_text(estado)
    cat = normalize_text(categoria)
    if "abono" in e or "devolucion" in e:
        return "abono"
    if "no valida" in e:
        return "venta_no_valida"
    if "regalo" in e or "regalo" in cat:
        return "regalo"
    if "baja" in e and (importe is None or abs(importe) < 0.01):
        return "baja_sin_importe"
    return None


def is_adw(*texts: object) -> bool:
    """Detecta Adwords / Google Ads a partir de uno o varios campos."""
    blob = " ".join(normalize_text(t) for t in texts)
    patterns = ("adw", "adwords", "google ads", "googleads", "ads")
    return any(p in blob for p in patterns)


def is_rns_subida(*texts: object) -> bool:
    """Detecta subida de precio RNS en varios formatos."""
    blob = " ".join(normalize_text(t) for t in texts)
    # Debe contener 'rns' o 'rn' acompanado de la idea de subida/renovacion.
    if "subida" in blob and ("rns" in blob or "rn " in blob or blob.strip().endswith("rn")):
        return True
    patterns = (
        "subida rns",
        "subida precio rns",
        "rns subida",
        "renovacion subida precio",
        "rn subida precio",
        "subida de precio rns",
    )
    return any(p in blob for p in patterns)


def is_upselling(*texts: object) -> bool:
    """Detecta upselling: 'upsell', 'upselling', 'up selling'."""
    blob = " ".join(normalize_text(t) for t in texts)
    compact = blob.replace(" ", "")
    return "upsell" in compact


def is_venta_fria(*texts: object) -> bool:
    """Detecta venta fria: 'fria', 'venta fria', 'nueva fria' (con o sin tilde)."""
    blob = " ".join(normalize_text(t) for t in texts)
    patterns = ("fria", "venta fria", "nueva fria")
    return any(p in blob for p in patterns)


def is_venta_nueva_499(importe: Optional[float], *texts: object) -> bool:
    """Detecta venta nueva de 499+ usando texto e importe.

    Debe haber indicio de 'venta nueva' / 'nueva' / '499' en el texto y un
    importe normalizado >= 499.
    """
    if importe is None or importe < 499:
        return False
    blob = " ".join(normalize_text(t) for t in texts)
    indicators = ("nueva", "venta nueva", "499", "alta", "nuevo")
    # Si hay importe >=499 y algun indicio de novedad, se considera venta nueva.
    return any(ind in blob for ind in indicators) or importe >= 499
