import { api } from "../api.js";

export async function renderTransactions(container) {
  container.innerHTML = `<p class="muted">Carregando transações…</p>`;

  const [transactions, categories, accounts] = await Promise.all([
    api.transactions.list(),
    api.categories.list(),
    api.accounts.list(),
  ]);

  const categoryName = (id) => categories.find((c) => c.id === id)?.name ?? "—";
  const accountName = (id) => accounts.find((a) => a.id === id)?.name ?? "—";

  const rows = transactions
    .map(
      (t) => `
      <tr>
        <td>${t.occurred_on}</td>
        <td>${t.description}</td>
        <td>${categoryName(t.category_id)}</td>
        <td>${accountName(t.account_id)}</td>
        <td class="${t.type === "expense" ? "negative" : "positive"}">
          ${t.type === "expense" ? "-" : "+"} R$ ${Number(t.amount).toFixed(2)}
        </td>
        <td><button data-id="${t.id}" class="btn-delete">Excluir</button></td>
      </tr>`
    )
    .join("");

  container.innerHTML = `
    <div class="toolbar">
      <button id="new-transaction-btn" class="btn-primary">+ Nova Transação</button>
    </div>
    <div class="transactions-container"><table class="data-table">
      <thead>
        <tr><th>Data</th><th>Descrição</th><th>Categoria</th><th>Conta</th><th>Valor</th><th></th></tr>
      </thead>
      <tbody>${rows || `<tr><td colspan="6" class="muted">Nenhuma transação registada ainda.</td></tr>`}</tbody>
    </table></div>
    <dialog id="transaction-dialog" class="transaction-dialog">
      <form id="transaction-form" method="dialog">
        <h3>Nova Transação</h3>
        <label>Descrição <input name="description" required /></label>
        <label>Valor <input name="amount" type="number" step="0.01" min="0.01" required /></label>
        <label>Tipo
          <select name="type">
            <option value="expense">Despesa</option>
            <option value="income">Receita</option>
            <option value="transfer">Transferência</option>
          </select>
        </label>
        <label>Data <input name="occurred_on" type="date" required /></label>
        <label>Categoria
          <select name="category_id">
            ${categories.map((c) => `<option value="${c.id}">${c.name}</option>`).join("")}
          </select>
        </label>
        <label>Conta
          <select name="account_id" required>
            ${accounts.map((a) => `<option value="${a.id}">${a.name}</option>`).join("")}
          </select>
        </label>
        <p class="form-hint">Movimentos recorrentes podem ser configurados na seção Recorrências.</p>
        <div class="dialog-actions">
          <button type="button" id="cancel-btn">Cancelar</button>
          <button type="submit" class="btn-primary">Salvar</button>
        </div>
      </form>
    </dialog>
  `;

  const dialog = container.querySelector("#transaction-dialog");
  container.querySelector("#new-transaction-btn").onclick = () => dialog.showModal();
  container.querySelector("#cancel-btn").onclick = () => dialog.close();

  container.querySelector("#transaction-form").onsubmit = async (e) => {
    const form = e.target;
    const data = Object.fromEntries(new FormData(form).entries());
    data.amount = parseFloat(data.amount);
    await api.transactions.create(data);
    renderTransactions(container);
  };

  container.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.onclick = async () => {
      await api.transactions.remove(btn.dataset.id);
      renderTransactions(container);
    };
  });
}
