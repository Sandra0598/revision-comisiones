# Revisión de Comisiones Comerciales

Aplicación web para revisar las **comisiones comerciales mensuales** de LOANGIA a
partir de un Excel de ventas: calcula concursos, comisiones, rappels, bonus y
diferencias, y genera un Excel final de revisión con pestañas por comercial,
resumen general, configuración e incidencias.

- `backend/` — API en **Python + FastAPI**. Procesa el Excel y genera el de
  revisión (pandas + openpyxl).
- `frontend/` — Interfaz en **React + TypeScript + Vite + Tailwind**.

## 🔗 Enlace en producción

- **Web:** https://comisiones-loangia-web.fly.dev
- **API:** https://comisiones-loangia-api.fly.dev

> El plan económico de Fly "duerme" las máquinas tras un rato sin uso; la primera
> visita tarda unos segundos en despertar. El enlace es permanente y funciona sin
> tener ningún ordenador encendido.

## Desarrollo local

Necesitas dos terminales:

```bash
# 1) Backend (http://localhost:8000)
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 2) Frontend (http://localhost:5180)
cd frontend
npm install
npm run dev
```

Abre http://localhost:5180. El frontend usa `VITE_API_URL` para localizar el
backend (ver `.env.local` / `.env.production`); en local, si está vacío, las
llamadas `/api` se redirigen al backend mediante el proxy de Vite.

## Despliegue (Fly.io)

La app se despliega como **dos apps en Fly**, mismo patrón que el proyecto de
bancos (`loangia-excel`):

| App | Dominio | Contenido |
|-----|---------|-----------|
| `comisiones-loangia-api` | comisiones-loangia-api.fly.dev | FastAPI en Docker (`backend/Dockerfile`) |
| `comisiones-loangia-web` | comisiones-loangia-web.fly.dev | Vite compilado y servido con nginx (`frontend/Dockerfile`) |

Ambas viven en la org **Edu** de Fly, región `cdg` (París).

### Volver a desplegar tras cambios

```bash
git add -A && git commit -m "..." && git push      # GitHub

# Backend
cd backend && fly deploy --remote-only

# Frontend
cd frontend && fly deploy --remote-only
```

### Configuración clave

- `frontend/.env.production` → `VITE_API_URL` apunta a la API en Fly.
- `backend/app/main.py` → CORS permite el dominio de la web (y orígenes locales);
  ampliable con la variable de entorno `CORS_ORIGINS`.
- `backend/fly.toml` → health check en `/health`.

## Privacidad

Los Excel con datos reales de ventas/comisiones **no** se suben al repositorio ni
a las imágenes de Docker (ver [`.gitignore`](.gitignore) y los `.dockerignore`).
La app arranca vacía: cada usuario sube su propio Excel.
