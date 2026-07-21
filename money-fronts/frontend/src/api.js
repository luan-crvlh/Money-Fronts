// Import obrigatório para a comunicação com o Rust
import { invoke } from '@tauri-apps/api/core'; 

// Removemos o "/api" daqui para evitar URLs duplicadas e permitir o /health na raiz
let baseUrl = "http://127.0.0.1:8756";
let isConfigured = false;

// Esta função substitui o seu "setupApi" e garante que o Rust seja 
// consultado apenas uma vez.
export async function resolveBaseUrl() {
  if (isConfigured) return baseUrl;

  try {
    const port = await invoke('get_backend_port');
    baseUrl = `http://127.0.0.1:${port}`;
    console.log(`Conectado ao backend na porta: ${port}`);
    isConfigured = true;
  } catch (error) {
    console.warn("Não está no ambiente Tauri. Usando porta padrão 8756.");
    isConfigured = true;
  }
  
  return baseUrl;
}

/** Aguarda o backend responder 200 em /health antes de liberar a UI (RN1 do ERSW). */
export async function waitForBackendHealth(maxAttempts = 40, intervalMs = 250) {
  const base = await resolveBaseUrl();
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      // Como o "base" não tem mais o "/api", o caminho gerado será perfeito: http://127.0.0.1:porta/health
      const res = await fetch(`${base}/health`);
      if (res.ok) return true;
    } catch (_) {
      // backend ainda não subiu; tenta novamente
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error("Backend não respondeu ao Health Check a tempo.");
}

async function request(path, options = {}) {
  const base = await resolveBaseUrl();
  
  // A concatenação agora ficará correta (ex: base + "/api/categories")
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Erro ${res.status} em ${path}: ${body}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  categories: {
    list: () => request("/api/categories"),
    create: (data) => request("/api/categories", { method: "POST", body: JSON.stringify(data) }),
    remove: (id) => request(`/api/categories/${id}`, { method: "DELETE" }),
  },
  accounts: {
    list: () => request("/api/accounts"),
    create: (data) => request("/api/accounts", { method: "POST", body: JSON.stringify(data) }),
    remove: (id) => request(`/api/accounts/${id}`, { method: "DELETE" }),
  },
  transactions: {
    list: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return request(`/api/transactions${qs ? `?${qs}` : ""}`);
    },
    create: (data) => request("/api/transactions", { method: "POST", body: JSON.stringify(data) }),
    update: (id, data) =>
      request(`/api/transactions/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    remove: (id) => request(`/api/transactions/${id}`, { method: "DELETE" }),
  },
  budgets: {
    list: (month, year) => request(`/api/budgets?month=${month}&year=${year}`),
    create: (data) => request("/api/budgets", { method: "POST", body: JSON.stringify(data) }),
    progress: (month, year) => request(`/api/budgets/progress?month=${month}&year=${year}`),
  },
  recurringRules: {
    list: () => request("/api/recurring-rules"),
    create: (data) => request("/api/recurring-rules", { method: "POST", body: JSON.stringify(data) }),
    remove: (id) => request(`/api/recurring-rules/${id}`, { method: "DELETE" }),
    generate: (month, year) => request(`/api/recurring-rules/generate?month=${month}&year=${year}`, { method: "POST" }),
  },
  dashboard: {
    summary: (month, year) => request(`/api/dashboard/summary?month=${month}&year=${year}`),
  },
};