import { api } from "../api.js";

export async function renderCategories(container) {
  container.innerHTML = `<p class="muted">Carregando categorias…</p>`;

  const categories = await api.categories.list();

  const items = categories
    .map(
      (c) => `
      <li class="category-item">
        <span class="color-dot" style="background:${c.color}"></span>
        ${c.name}
        <span class="tag">${c.budget_group}</span>
        ${!c.is_system ? `<button data-id="${c.id}" class="btn-delete">×</button>` : ""}
      </li>`
    )
    .join("");

  container.innerHTML = `
    <div class="toolbar">
      <button id="new-category-btn" class="btn-primary">+ Nova Categoria</button>
    </div>
    <ul class="category-list">${items}</ul>
    <dialog id="category-dialog">
      <form id="category-form" method="dialog">
        <h3>Nova Categoria</h3>
        <label>Nome <input name="name" required /></label>
        <label>Cor <input name="color" type="color" value="#6366F1" /></label>
        <label>Grupo (Regra 50/30/20)
          <select name="budget_group">
            <option value="needs">Necessidades</option>
            <option value="wants">Desejos</option>
            <option value="savings">Investimentos/Dívidas</option>
          </select>
        </label>
        <div class="dialog-actions">
          <button type="button" id="cancel-btn">Cancelar</button>
          <button type="submit" class="btn-primary">Salvar</button>
        </div>
      </form>
    </dialog>
  `;

  const dialog = container.querySelector("#category-dialog");
  container.querySelector("#new-category-btn").onclick = () => dialog.showModal();
  container.querySelector("#cancel-btn").onclick = () => dialog.close();

  container.querySelector("#category-form").onsubmit = async (e) => {
    const data = Object.fromEntries(new FormData(e.target).entries());
    await api.categories.create(data);
    renderCategories(container);
  };

  container.querySelectorAll(".btn-delete").forEach((btn) => {
    btn.onclick = async () => {
      await api.categories.remove(btn.dataset.id);
      renderCategories(container);
    };
  });
}
