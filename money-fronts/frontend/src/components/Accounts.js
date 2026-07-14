import { api } from "../api.js";

const ACCOUNT_TYPES = {
  checking: "Conta corrente", savings: "Poupança", credit: "Cartão de crédito",
  cash: "Dinheiro", investment: "Investimentos",
};

export async function renderAccounts(container) {
  container.innerHTML = `<p class="muted">Carregando contas…</p>`;
  const accounts = await api.accounts.list();
  container.innerHTML = `
    <header class="page-heading"><div><p class="eyebrow">Sua estrutura financeira</p><h2>Contas</h2><p class="muted">Cadastre bancos, carteiras e investimentos para atribuir cada movimento à origem correta.</p></div><button id="new-account-btn" class="btn-primary">+ Nova conta</button></header>
    <section class="accounts-grid">${accounts.map((account) => `<article class="account-card"><div class="account-symbol">${account.name.slice(0, 1).toUpperCase()}</div><div><strong>${account.name}</strong><p>${account.institution || "Instituição não informada"}</p><span class="tag">${ACCOUNT_TYPES[account.account_type] || account.account_type}</span></div><div class="account-balance">R$ ${Number(account.initial_balance).toFixed(2)}<small>saldo inicial</small></div><button class="btn-delete" data-id="${account.id}">Excluir</button></article>`).join("") || `<p class="muted">Nenhuma conta cadastrada. Crie uma conta para registrar transações e recorrências.</p>`}</section>
    <dialog id="account-dialog" class="transaction-dialog"><form id="account-form" method="dialog"><h3>Nova conta</h3><label>Nome da conta <input name="name" placeholder="Ex.: Minha conta principal" required /></label><label>Banco ou instituição <input name="institution" placeholder="Ex.: Nubank, Itaú ou carteira" /></label><label>Tipo <select name="account_type"><option value="checking">Conta corrente</option><option value="savings">Poupança</option><option value="credit">Cartão de crédito</option><option value="cash">Dinheiro</option><option value="investment">Investimentos</option></select></label><label>Saldo inicial <input name="initial_balance" type="number" step="0.01" value="0" required /></label><p class="form-hint">O saldo inicial serve como ponto de partida; as transações serão vinculadas a esta conta.</p><div class="dialog-actions"><button id="cancel-account" type="button">Cancelar</button><button class="btn-primary" type="submit">Salvar conta</button></div></form></dialog>`;

  const dialog = container.querySelector("#account-dialog");
  container.querySelector("#new-account-btn").onclick = () => dialog.showModal();
  container.querySelector("#cancel-account").onclick = () => dialog.close();
  container.querySelector("#account-form").onsubmit = async (event) => {
    const data = Object.fromEntries(new FormData(event.target).entries());
    data.initial_balance = Number(data.initial_balance);
    if (!data.institution) data.institution = null;
    await api.accounts.create(data);
    renderAccounts(container);
  };
  container.querySelectorAll(".btn-delete").forEach((button) => {
    button.onclick = async () => { await api.accounts.remove(button.dataset.id); renderAccounts(container); };
  });
}
