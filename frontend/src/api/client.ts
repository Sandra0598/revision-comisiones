import axios from "axios";

// baseURL configurable por VITE_API_URL; por defecto el backend local.
export const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});
