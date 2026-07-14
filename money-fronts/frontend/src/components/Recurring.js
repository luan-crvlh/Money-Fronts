import { api } from "../api.js";

export async function renderRecurring(container) {
  container.innerHTML = `<p class="muted">Carregando recorrências…</p>`;
  const [rules, categories, accounts] = await Promise.all([
    api.recurringRules.list(), api.categories.list(), api.accounts.list(),
  ]);
  const categoryName = (id) => categories.find((category) => category.id === id)?.name ?? "Sem categoria";
  const accountName = (id) => accounts.find((account) => account.id === id)?.name ?? "—";

  container.innerHTML = `
    <header class="page-heading"><div><p class="eyebrow">Planejamento automático</p><h2>Recorrências</h2><p class="muted">Crie lançamentos mensais para contas, assinaturas e receitas fixas.</p></div><div class="toolbar"><button id="generate-rules" class="btn-secondary">Gerar mês atual</button><button id="new-rule-btn" class="btn-primary">+ Nova recorrência</button></div></header>
    <div class="recurring-grid">${rules.map((rule) => `<article class="recurring-card"><div class="recurring-icon">↻</div><div><strong>${rule.description}</strong><p>${rule.type === "income" ? "Receita" : "Despesa"} · todo dia ${rule.day_of_month}</p><small>${categoryName(rule.category_id)} · ${accountName(rule.account_id)}</small></div><div class="recurring-value ${rule.type === "expense" ? "negative" : "positive"}">R$ ${Number(rule.amount).toFixed(2)}</div><button class="btn-delete" data-id="${rule.id}">Excluir</button></article>`).join("") || `<p class="muted">Nenhuma recorrência configurada.</p>`}</div>
    <dialog id="recurring-dialog" class="transaction-dialog"><form id="recurring-form" method="dialog"><h3>Nova recorrência</h3><label>Descrição <input name="description" required /></label><label>Valor <input name="amount" type="number" step="0.01" min="0.01" required /></label><label>Tipo <select name="type"><option value="expense">Despesa</option><option value="income">Receita</option></select></label><label>Dia do mês <input name="day_of_month" type="number" min="1" max="28" required /></label><label>Categoria <select name="category_id"><option value="">Sem categoria</option>${categories.map((category) => `<option value="${category.id}">${category.name}</option>`).join("")}</select></label><label>Conta <select name="account_id" required>${accounts.map((account) => `<option value="${account.id}">${account.name}</option>`).join("")}</select></label><div class="dialog-actions"><button type="button" id="cancel-rule">Cancelar</button><button class="btn-primary" type="submit">Salvar</button></div></form></dialog>`;

  const dialog = container.querySelector("#recurring-dialog");
  container.querySelector("#new-rule-btn").onclick = () => dialog.showModal();
  container.querySelector("#cancel-rule").onclick = () => dialog.close();
  container.querySelector("#recurring-form").onsubmit = async (event) => {
    const data = Object.fromEntries(new FormData(event.target).entries());
    data.amount = Number(data.amount); data.day_of_month = Number(data.day_of_month);
    if (!data.category_id) data.category_id = null;
    await api.recurringRules.create(data);
    renderRecurring(container);
  };
  container.querySelector("#generate-rules").onclick = async () => {
    const now = new Date();
    await api.recurringRules.generate(now.getMonth() + 1, now.getFullYear());
    renderRecurring(container);
  };
  container.querySelectorAll(".btn-delete").forEach((button) => {
    button.onclick = async () => { await api.recurringRules.remove(button.dataset.id); renderRecurring(container); };
  });
}
