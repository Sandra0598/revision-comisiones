# Revisión de Comisiones Comerciales — Backend

Backend en **FastAPI** que recibe un Excel mensual de ventas comerciales, calcula
automáticamente concursos, comisiones, rappels, bonus y diferencias, y genera un
Excel final de revisión con pestañas por comercial, resumen general, configuración
e incidencias.

El sistema revisa las ventas del **mes anterior**. El mes/año puede inferirse de
las fechas del Excel o indicarse manualmente desde el frontend.

## Stack

- Python 3.11+
- FastAPI
- pandas
- openpyxl
- pydantic
- python-multipart
- uvicorn

## Estructura

```
backend/
  app/
    main.py                      # API y endpoints
    models/
      schemas.py                 # modelos pydantic
    services/
      excel_reader.py            # lectura del Excel + mapeo de filas
      column_mapper.py           # mapeo de columnas por similitud
      validators.py              # clasificación de filas y validaciones
      commission_engine.py       # motor de cálculo de comisiones
      excel_writer.py            # generación del Excel final (openpyxl)
    data/
      config_defaults.py         # configuración por defecto editable
      tables.py                  # tablas de rappel y super concurso
    utils/
      normalize.py               # normalización de texto, importes y tipos
  tmp/                           # Excels generados (temporales)
  requirements.txt
  README.md
```

## Instalación

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`. Documentación interactiva en
`http://localhost:8000/docs`.

CORS permitido para `http://localhost:5173` y `http://localhost:3000`.

## Endpoints

### `POST /api/analyze`

Analiza el Excel y genera el de revisión.

- `file` (multipart): Excel de ventas (`.xlsx`/`.xls`).
- `config` (form, opcional): JSON con la configuración editable.
- `mes` (form, opcional): mes de revisión (1-12).
- `anio` (form, opcional): año de revisión.

Respuesta JSON: resumen calculado por comercial, datos de la pareja, incidencias
y el `nombre_archivo` temporal del Excel generado.

Ejemplo con `curl`:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "file=@ventas_abril.xlsx" \
  -F 'config={"importe_concurso_mensual": 1000, "autorizacion_raul": "Sí"}' \
  -F "mes=4" -F "anio=2026"
```

### `GET /api/download/{filename}`

Descarga el Excel final generado. Usa el `nombre_archivo` devuelto por `/api/analyze`.

```bash
curl -OJ http://localhost:8000/api/download/<nombre_archivo>
```

### `GET /api/config/defaults`

Devuelve la configuración por defecto editable.

## Configuración editable

| Campo | Por defecto |
|---|---|
| `importe_concurso_mensual` | 0 (editable) |
| `premio_ventas_nuevas_499` | 225 |
| `minimo_ventas_nuevas_499` | 6 |
| `ventas_obligatorias_individual` | 25 |
| `ventas_obligatorias_pareja` | 50 |
| `objetivo_pizarra_1` | 13 |
| `objetivo_pizarra_2` | 12 |
| `referencia_frias_100` | 13 |
| `referencia_upselling_100` | 7 |
| `equivalencia_upselling_a_fria` | 0.5 |
| `adw_bloque_para_punto` | 3 |
| `rns_bloque_para_punto` | 4 |
| `importe_venta_doble` | 859 |
| `activar_venta_doble_859` | true |
| `aplicar_premios_solo_si_100_concurso` | true |
| `modalidad_porcentaje_concurso` | "pizarra_1_y_pizarra_2" |
| `pareja_fija` | ["Eva", "Sara"] |
| `autorizacion_raul` | "Sí" / "No" / "Pendiente" |

Datos auxiliares opcionales en el JSON de configuración:

- `meses_consecutivos_individual`: `{"Eva": 2, "Marta": 1, ...}`
- `mes_consecutivo_pareja`: `1 | 2 | 3 | "siguientes"`
- `nivel_pareja_mes_anterior`, `nivel_pareja_actual`: `"Baby" | "Junior" | "Senior"`
- `mes_revision`, `anio_revision`

## Reglas de negocio implementadas

- **Mapeo de columnas por similitud** a campos internos; incidencia si falta una
  imprescindible (`comercial`, `tipo_venta`, `importe_venta`).
- **Venta doble**: importe exactamente 859 → vale por 2 (si está activada).
- **Pizarra 1** = ventas computables reales P1. **Pizarra 2 ajustada** =
  ventas reales P2 + `floor(ADW/3)` + `floor(RNS/4)`.
- **Puntos ADW** en hitos de 3, **puntos RNS** en hitos de 4; solo suman a Pizarra 2.
- **% concurso** = `min(((min(P1/13,1) + min(P2aj/12,1))/2)*100, 100)`; 100 si
  ambas pizarras cumplen objetivo.
- **Equivalencia**: 1 fría = 2 upselling (dato auxiliar visible).
- **Premios adicionales** (499+, rappel bonus, rappel individual, super concurso)
  solo si `% concurso ≥ 100`.
- **Tablas individuales**: se restan 25 ventas antes de consultar. **Pareja**: 50.
- **Rappel individual** por niveles (baby…4.0) según mes consecutivo. Se aplica
  a todas las comerciales **excepto Eva y Sara**: en ellas el rappel en pareja
  sustituye al rappel individual.
- **Suma de rappels**:
  - Resto de comerciales: `rappel bonus general + rappel individual`.
  - Eva y Sara: `rappel bonus general + super concurso de pareja` (cada una),
    sin rappel individual.
- **Super concurso pareja Eva+Sara**: se calcula una vez y se suma a cada una.
  Requiere que ambas lleguen al 100%. Subida de nivel requiere autorización de Raúl.
- **Comisión declarada**: diferencia y estado (`Correcta` / `Declarada de más` /
  `Declarada de menos` / `No comprobable`).

## Excel de salida

`Revision_Comisiones_[Mes]_[Año].xlsx` con pestañas:

1. Configuración
2. Resumen general
3. Una por cada comercial
4. Eva
5. Sara
6. Concurso Pareja Eva-Sara
7. Incidencias

Estilos: cabeceras en negrita, autofiltro, ancho automático, formato moneda y
porcentaje, y resaltado por estado/gravedad.
```
