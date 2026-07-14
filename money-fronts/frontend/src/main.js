import { waitForBackendHealth } from "./api.js";
import { renderDashboard } from "./components/Dashboard.js";
import { renderTransactions } from "./components/Transactions.js";
import { renderCategories } from "./components/Categories.js";
import { renderRecurring } from "./components/Recurring.js";
import { renderAccounts } from "./components/Accounts.js";

const routes = {
  dashboard: { label: "Dashboard", render: renderDashboard },
  transactions: { label: "Transações", render: renderTransactions },
  categories: { label: "Categorias", render: renderCategories },
  accounts: { label: "Contas", render: renderAccounts },
  recurring: { label: "Recorrências", render: renderRecurring },
};

function renderShell() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="layout">
      <nav class="sidebar">
        <h1>Money Fronts</h1>
        <ul>
          ${Object.entries(routes)
            .map(([key, r]) => `<li><a href="#${key}" data-route="${key}">${r.label}</a></li>`)
            .join("")}
        </ul>
      </nav>
      <main id="view"></main>
    </div>
  `;
}

async function navigate() {
  const view = document.getElementById("view");
  const routeKey = location.hash.replace("#", "") || "dashboard";
  const route = routes[routeKey] ?? routes.dashboard;

  document.querySelectorAll("[data-route]").forEach((el) => {
    el.classList.toggle("active", el.dataset.route === routeKey);
  });

  try {
    await route.render(view);
  } catch (err) {
    view.innerHTML = `<p class="error">Erro ao carregar: ${err.message}</p>`;
  }
}

async function bootstrap() {
  const boot = document.getElementById("boot-screen");
  try {
    // RN1 do ERSW: só exibe os painéis após HTTP 200 do backend.
    await waitForBackendHealth();
    renderShell();
    window.addEventListener("hashchange", navigate);
    await navigate();
  } catch (err) {
    boot.innerHTML = `<p class="error">Não foi possível conectar ao backend local: ${err.message}</p>`;
  }
}

bootstrap();
