// Camada de comunicação HTTP com o Sidecar Python (DAS seção 2).
// A porta é dinâmica; o Rust a expõe via comando `get_backend_port` (invoke).

let baseUrl = null;

async function resolveBaseUrl() {
  if (baseUrl) return baseUrl;

  // Em produção (dentro do Tauri), pergunta ao Rust qual porta foi escolhida.
  if (window.__TAURI__) {
    const { invoke } = window.__TAURI__.core;
    const port = await invoke("get_backend_port");
    baseUrl = `http://127.0.0.1:${port}`;
  } else {
    // Modo dev standalone (fora do Tauri): assume a porta fixa de fallback do main.py
    baseUrl = "http://127.0.0.1:8756";
  }
  return baseUrl;
}

/** Aguarda o backend responder 200 em /health antes de liberar a UI (RN1 do ERSW). */
export async function waitForBackendHealth(maxAttempts = 40, intervalMs = 250) {
  const base = await resolveBaseUrl();
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
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
  dashboard: {
    summary: (month, year) => request(`/api/dashboard/summary?month=${month}&year=${year}`),
  },
};
