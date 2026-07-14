import { api } from "../api.js";

const GROUP_LABELS = { needs: "Necessidades", wants: "Desejos", savings: "Investimentos/Dívidas" };

const money = (value) => `R$ ${Number(value).toFixed(2)}`;

function categoryChart(categories, mode) {
  const total = categories.reduce((sum, item) => sum + Number(item.amount), 0);
  if (!total) return `<p class="muted empty-chart">Registre despesas para visualizar a distribuição por categoria.</p>`;

  if (mode === "bars") {
    return `<div class="category-bars">${categories.map((item) => {
      const percent = (Number(item.amount) / total) * 100;
      return `<div class="category-bar-row"><span class="category-label"><i style="background:${item.color}"></i>${item.category_name}</span><div class="category-bar-track"><div class="category-bar-value" style="width:${percent}%;background:${item.color}"></div></div><strong>${money(item.amount)}</strong></div>`;
    }).join("")}</div>`;
  }

  let position = 0;
  const slices = categories.map((item) => {
    const end = position + (Number(item.amount) / total) * 100;
    const value = `${item.color} ${position.toFixed(2)}% ${end.toFixed(2)}%`;
    position = end;
    return value;
  });
  return `<div class="donut-layout"><div class="donut" role="img" aria-label="Divisão de despesas por categoria" style="background:conic-gradient(${slices.join(",")})"><span>${money(total)}<small>em despesas</small></span></div><ul class="chart-legend">${categories.map((item) => `<li><i style="background:${item.color}"></i><span>${item.category_name}</span><strong>${((Number(item.amount) / total) * 100).toFixed(0)}%</strong></li>`).join("")}</ul></div>`;
}

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
    <header class="page-heading"><div><p class="eyebrow">Visão do mês</p><h2>Olá, organize o seu dinheiro</h2></div><span class="month-chip">${now.toLocaleDateString("pt-BR", { month: "long", year: "numeric" })}</span></header>
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
    <section class="chart-section">
      <div class="section-heading"><div><h2>Gastos por categoria</h2><p class="muted">Acompanhe onde seu dinheiro foi usado.</p></div><label class="chart-switch">Visualização <select id="category-chart-mode"><option value="donut">Setores</option><option value="bars">Barras</option></select></label></div>
      <div id="category-chart">${categoryChart(summary.category_expenses, "donut")}</div>
    </section>
  `;

  container.querySelector("#category-chart-mode").onchange = (event) => {
    container.querySelector("#category-chart").innerHTML = categoryChart(summary.category_expenses, event.target.value);
  };
}
