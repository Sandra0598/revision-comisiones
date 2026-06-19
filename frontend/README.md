# Revisión de Comisiones Comerciales — Frontend

Interfaz web en **React + Vite + TypeScript + TailwindCSS** para subir el Excel
mensual de ventas, configurar parámetros, analizarlo con el backend y descargar
el Excel final de revisión.

## Stack

- React 18 + Vite + TypeScript
- TailwindCSS
- Axios
- Recharts (gráfico de totales por comercial)

## Estructura

```
frontend/
  src/
    main.tsx
    App.tsx                       # pantalla principal y orquestación
    api/
      client.ts                   # cliente Axios (baseURL configurable)
      commissionApi.ts            # getDefaultConfig / analyzeCommissions / downloadReport + adaptadores
    components/
      Layout.tsx                  # cabecera + Card reutilizable
      FileUpload.tsx              # drag & drop / input file (.xlsx/.xls)
      ConfigForm.tsx              # panel desplegable de configuración
      ResultsSummary.tsx          # resumen general + gráfico
      CommercialTable.tsx         # tabla por comercial con badges de estado
      PairContestCard.tsx         # card del super concurso Eva + Sara
      IncidentsTable.tsx          # tabla de incidencias
      DownloadBox.tsx             # descarga del Excel
      RulesAccordion.tsx          # bloque "Reglas aplicadas"
    types/commission.ts           # tipos del dominio
    utils/formatters.ts           # formatCurrency / formatPercent / formatNumber
  package.json
  vite.config.ts
  tailwind.config.js
  postcss.config.js
  README.md
```

## Instalación y ejecución

```bash
cd frontend
npm install
npm run dev
```

La app queda disponible en **http://localhost:5180**.

## Configuración del backend

Por defecto apunta a `http://localhost:8000`. Para cambiarlo, crea un archivo
`.env` (puedes copiar `.env.example`):

```
VITE_API_URL=http://localhost:8000
```

El backend debe exponer:

- `GET /api/config/defaults`
- `POST /api/analyze` (multipart/form-data: `file`, `config`, `mes`, `anio`)
- `GET /api/download/{filename}`

> El backend incluye CORS para `http://localhost:5180`.

## Flujo de uso

1. **Sube** el Excel mensual de ventas (.xlsx/.xls).
2. **Configura** los parámetros (se cargan los valores por defecto del backend).
   Opcionalmente, indica el mes/año a revisar, el mes consecutivo individual por
   comercial, el de la pareja y la autorización de Raúl.
3. Pulsa **Analizar comisiones**. Se muestra un indicador de carga y se bloquea
   el doble envío.
4. Revisa el **resumen general**, la **card de Eva + Sara** y las **incidencias**.
5. **Descarga** el Excel revisado.

## Reglas reflejadas en la interfaz

El bloque **"Reglas aplicadas"** explica de forma explícita:

- Venta de **859 €** = 2 ventas computables.
- **Pizarra 1** necesita 13 ventas; **Pizarra 2** necesita 12 (más puntos ADW/RNS).
- **ADW**: suma punto solo en la 3.ª, 6.ª, 9.ª… (hitos de 3).
- **RNS**: suma punto solo en la 4.ª, 8.ª, 12.ª… (hitos de 4).
- Antes de tablas individuales se restan **25** ventas.
- En la pareja Eva + Sara se restan **50** ventas.
- **Eva y Sara** tienen comisiones y pestañas separadas; el super concurso de
  pareja se calcula una vez y se suma a cada una.

## Validación de frontend

Antes de enviar se comprueba: que haya archivo, que sea `.xlsx`/`.xls`, que
`importe_concurso_mensual ≥ 0` y que la autorización de Raúl sea
`Sí` / `No` / `Pendiente`.
