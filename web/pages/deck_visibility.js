// Future deck-list enhancement. Import/call mountDeckVisibility after Access
// login and authenticated deck API integration; not loaded by production index.html.
// Server performs authorization and persists visibility. Never use this as a security gate.
export async function mountDeckVisibility(root, { apiBase = "", fetchImpl = fetch } = {}) {
  if (!root) throw new Error("Deck visibility root required");
  const endpoint = apiBase.replace(/\/$/, "");
  async function api(path, options) {
    const response = await fetchImpl(endpoint + path, { credentials: "include", ...options });
    if (!response.ok) throw new Error("Deck API returned " + response.status);
    return response.json();
  }
  async function render() {
    const { decks } = await api("/v1/decks");
    root.replaceChildren();
    const list = document.createElement("ul");
    for (const deck of decks) {
      const li = document.createElement("li");
      const label = document.createElement("span");
      label.textContent = deck.label + " ";
      li.append(label);
      if (deck.can_edit) {
        const wrap = document.createElement("label");
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = deck.visibility === "community";
        checkbox.setAttribute("aria-label", "Share " + deck.label + " with invited members");
        wrap.append(checkbox, document.createTextNode(" Public to members"));
        const error = document.createElement("span");
        error.setAttribute("role", "status");
        checkbox.addEventListener("change", async () => {
          checkbox.disabled = true;
          error.textContent = "";
          try {
            await api("/v1/decks/" + encodeURIComponent(deck.id) + "/visibility", {
              method: "PATCH",
              headers: { "content-type": "application/json" },
              body: JSON.stringify({ visibility: checkbox.checked ? "community" : "private" })
            });
          } catch {
            checkbox.checked = !checkbox.checked;
            error.textContent = "Could not save visibility";
          } finally { checkbox.disabled = false; }
        });
        li.append(wrap, error);
      } else {
        const status = document.createElement("span");
        status.textContent = "Shared";
        li.append(status);
      }
      list.append(li);
    }
    root.append(list);
  }
  await render();
}
