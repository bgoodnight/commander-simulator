-- Development D1 schema. Apply ONLY to an isolated database, never production.
-- Public means shared with signed-in invited members, not anonymous internet users.
CREATE TABLE IF NOT EXISTS decks (
  id TEXT PRIMARY KEY NOT NULL,
  label TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  visibility TEXT NOT NULL DEFAULT 'private'
    CHECK (visibility IN ('private', 'community')),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_decks_visibility ON decks (visibility);
CREATE INDEX IF NOT EXISTS idx_decks_owner ON decks (owner_id);
-- Transitional catalog seeds. No application-level hardcoded community list.
-- Private storage migration is REQUIRED before revoking public URL access to
-- existing decklists: toggles cannot hide content already on GitHub Pages.
INSERT OR IGNORE INTO decks (id, label, owner_id, visibility) VALUES
  ('magnus_premium', 'Magnus the Red', 'site-owner', 'community'),
  ('mortarion_current', 'Mortarion', 'site-owner', 'community');
