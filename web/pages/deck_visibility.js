// Future *unmounted* deck-list UI. Replaces the unsafe public/private toggle
// with publication actions. No live production site references this file.
// Wiring is deferred until authenticated snapshot write APIs are implemented.
export function mountPublicationControls(root, decks, handlers = {}) {
  if (!root) throw new Error("Publication controls root required");
  root.replaceChildren();
  const list = document.createElement("ul");
  for (const deck of decks) {
    const item = document.createElement("li");
    const name = document.createElement("span");
    name.textContent = deck.label;
    item.append(name);
    if (deck.can_edit) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Publish snapshot";
      button.disabled = typeof handlers.publish !== "function";
      button.addEventListener("click", () => handlers.publish?.(deck.id));
      item.append(button);
    }
    list.append(item);
  }
  root.append(list);
}
// A future publication detail view should expose Replace (new revision),
// Remove from Community (unlist), and Copy to My Decks. Never mutate a revision.
