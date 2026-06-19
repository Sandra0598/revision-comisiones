# syntax=docker/dockerfile:1

# --- Build: compila la SPA de Vite ---
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
# Usa .env.production (VITE_API_URL apunta al backend en Fly).
RUN npm run build

# --- Runtime: sirve los estáticos con nginx ---
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
