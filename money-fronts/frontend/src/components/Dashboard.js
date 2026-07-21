import { api } from "../api.js";

const GROUP_LABELS = { needs: "Necessidades", wants: "Desejos", savings: "Investimentos/Dívidas" };

const money = (value) => `R$ ${Number(value).toFixed(2)}`;

function categoryChart(categories, mode) {
  if (!Array.isArray(categories)) categories = [];
  
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

export async function renderDashboard(
  container, 
  selectedAccountId = "all", 
  selectedMonth = new Date().getMonth() + 1, 
  selectedYear = new Date().getFullYear()
) {
  container.innerHTML = `<p class="muted">Carregando dashboard…</p>`;

  try {
    const portaDinamica = window.localStorage.getItem('backend_port') || '8756';
    const baseUrl = `http://127.0.0.1:${portaDinamica}`;

    // 1. Busca as contas para o filtro
    const accountsRes = await fetch(`${baseUrl}/api/accounts`);
    const accounts = await accountsRes.json();
    const accountOptions = (Array.isArray(accounts) ? accounts : []).map(acc => 
      `<option value="${acc.id}" ${acc.id === selectedAccountId ? 'selected' : ''}>💳 ${acc.name}</option>`
    ).join("");

    // 2. Busca o resumo passando a data
    let summaryUrl = `${baseUrl}/api/dashboard/summary?month=${selectedMonth}&year=${selectedYear}`;
    if (selectedAccountId !== "all") {
      summaryUrl += `&account_id=${selectedAccountId}`;
    }
    
    const summaryRes = await fetch(summaryUrl);
    if (!summaryRes.ok) {
      const errorData = await summaryRes.json().catch(() => ({}));
      throw new Error(errorData.detail || `Falha no servidor (Erro ${summaryRes.status})`);
    }
    
    const summary = await summaryRes.json();

    const ruleRows = (summary.rule_50_30_20 || [])
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

    const totalInc = summary.total_income || 0;
    const totalExp = summary.total_expense || 0;
    const netBalance = summary.net_balance ?? summary.monthly_balance ?? 0;
    const safeSpend = summary.safe_to_spend_daily || 0;

    const currBalance = summary.current_balance || 0;
    const catExpenses = summary.category_expenses || summary.expenses_by_category || [];

    const mappedCategories = catExpenses.map(c => ({
      ...c,
      amount: c.amount ?? c.total ?? 0,
      category_name: c.category_name ?? c.name ?? "Desconhecida"
    }));

    // 3. Constrói as opções dos meses
    const meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    const monthOptions = meses.map((mes, index) => {
      const valorMes = index + 1;
      return `<option value="${valorMes}" ${valorMes === selectedMonth ? 'selected' : ''}>${mes}</option>`;
    }).join("");

    // 4. Constrói as opções dos anos (ex: de 2020 até 2030)
    let yearOptions = "";
    for (let y = 2020; y <= 2030; y++) {
      yearOptions += `<option value="${y}" ${y === selectedYear ? 'selected' : ''}>${y}</option>`;
    }

    // VARIÁVEL DE ESTILO UNIFICADA PARA OS SELECTS
    const selectStyle = "padding: 8px 12px; border-radius: 6px; border: 1px solid #374151; cursor: pointer; background-color: #1f2937; color: #f9fafb; font-size: 14px; outline: none;";

    container.innerHTML = `
      <header class="page-heading">
        <div>
          <p class="eyebrow">Visão do mês</p>
          <h2>Olá, organize o seu dinheiro</h2>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
          <!-- Filtro de Conta -->
          <select id="account-filter" style="${selectStyle}">
            <option value="all">Todas as Contas</option>
            ${accountOptions}
          </select>
          
          <!-- Filtro de Mês -->
          <select id="month-filter" style="${selectStyle}">
            ${monthOptions}
          </select>

          <!-- Filtro de Ano -->
          <select id="year-filter" style="${selectStyle}">
            ${yearOptions}
          </select>
        </div>
      </header>
      
      <section class="cards">
        <!-- NOVO CARD: Saldo Geral/Atual -->
        <div class="card" style="border: 1px solid #374151; background-color: #111827;">
          <h3>Saldo Atual</h3>
          <p class="value ${currBalance >= 0 ? "positive" : "negative"}">R$ ${currBalance.toFixed(2)}</p>
        </div>

        <div class="card">
          <h3>Receitas (Mês)</h3>
          <p class="value positive">R$ ${totalInc.toFixed(2)}</p>
        </div>
        <div class="card">
          <h3>Despesas (Mês)</h3>
          <p class="value negative">R$ ${totalExp.toFixed(2)}</p>
        </div>
        <div class="card">
          <h3>Saldo Líquido (Mês)</h3>
          <p class="value ${netBalance >= 0 ? "positive" : "negative"}">R$ ${netBalance.toFixed(2)}</p>
        </div>
        <div class="card">
          <h3>Livre / Dia (Mês)</h3>
          <p class="value">R$ ${safeSpend.toFixed(2)}</p>
        </div>
      </section>

      <section>
        <h2>Regra 50/30/20</h2>
        ${ruleRows || '<p class="muted">Os dados da regra não estão disponíveis no momento.</p>'}
      </section>
      <section class="chart-section">
        <div class="section-heading"><div><h2>Gastos por categoria</h2><p class="muted">Acompanhe onde seu dinheiro foi usado.</p></div><label class="chart-switch">Visualização <select id="category-chart-mode"><option value="donut">Setores</option><option value="bars">Barras</option></select></label></div>
        <div id="category-chart">${categoryChart(mappedCategories, "donut")}</div>
      </section>
    `;

    // Eventos dos gráficos
    container.querySelector("#category-chart-mode").onchange = (event) => {
      container.querySelector("#category-chart").innerHTML = categoryChart(mappedCategories, event.target.value);
    };

    // Eventos de alteração dos filtros
    container.querySelector("#account-filter").onchange = (event) => {
      renderDashboard(container, event.target.value, selectedMonth, selectedYear);
    };

    container.querySelector("#month-filter").onchange = (event) => {
      const newMonth = parseInt(event.target.value, 10);
      renderDashboard(container, selectedAccountId, newMonth, selectedYear);
    };

    container.querySelector("#year-filter").onchange = (event) => {
      const newYear = parseInt(event.target.value, 10);
      renderDashboard(container, selectedAccountId, selectedMonth, newYear);
    };

  } catch (error) {
    console.error("Erro ao renderizar Dashboard:", error);
    container.innerHTML = `<p class="error">Erro ao carregar o dashboard: ${error.message}</p>`;
  }
}