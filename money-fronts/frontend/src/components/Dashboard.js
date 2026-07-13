import { api } from "../api.js";

const GROUP_LABELS = { needs: "Necessidades", wants: "Desejos", savings: "Investimentos/Dívidas" };

export async function renderDashboard(container) {
  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();

  container.innerHTML = `<p class="muted">Carregando dashboard…</p>`;

  const summary = await api.dashboard.summary(month, year);

  const ruleRows = summary.rule_50_30_20
    .map(
      (r) => `
      <div class="rule-row">
        <span>${GROUP_LABELS[r.group] ?? r.group}</span>
        <div class="bar">
          <div class="bar-fill" style="width:${Math.min(r.actual_percentage, 100)}%"></div>
        </div>
        <span class="muted">${r.actual_percentage.toFixed(1)}% (meta ${r.planned_percentage.toFixed(0)}%)</span>
      </div>`
    )
    .join("");

  container.innerHTML = `
    <section class="cards">
      <div class="card">
        <h3>Receitas</h3>
        <p class="value positive">R$ ${summary.total_income.toFixed(2)}</p>
      </div>
      <div class="card">
        <h3>Despesas</h3>
        <p class="value negative">R$ ${summary.total_expense.toFixed(2)}</p>
      </div>
      <div class="card">
        <h3>Saldo Líquido</h3>
        <p class="value ${summary.net_balance >= 0 ? "positive" : "negative"}">R$ ${summary.net_balance.toFixed(2)}</p>
      </div>
      <div class="card">
        <h3>Livre para Gastar / Dia</h3>
        <p class="value">R$ ${summary.safe_to_spend_daily.toFixed(2)}</p>
      </div>
    </section>

    <section>
      <h2>Regra 50/30/20</h2>
      ${ruleRows}
    </section>
  `;
}
