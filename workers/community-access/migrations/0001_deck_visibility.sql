-- New isolated development D1 database only. Do not apply to production.
-- Current GitHub Pages decklists are public until migrated out of static assets.
CREATE TABLE IF NOT EXISTS decks (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  label TEXT NOT NULL,
  private_content_key TEXT NOT NULL,
  content_sha256 TEXT NOT NULL CHECK(length(content_sha256)=64),
  revision INTEGER NOT NULL DEFAULT 1 CHECK(revision >= 1),
  source_publication_revision_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_decks_owner ON decks(owner_id);

CREATE TABLE IF NOT EXISTS publications (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  source_deck_id TEXT,
  label TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'listed' CHECK(status IN ('listed','unlisted')),
  current_revision_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_publications_listed ON publications(status);

CREATE TABLE IF NOT EXISTS publication_revisions (
  id TEXT PRIMARY KEY,
  publication_id TEXT NOT NULL REFERENCES publications(id),
  revision_no INTEGER NOT NULL CHECK(revision_no > 0),
  content_sha256 TEXT NOT NULL CHECK(length(content_sha256)=64),
  immutable_content_key TEXT NOT NULL,
  source_deck_revision TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(publication_id,revision_no)
);
-- Revisions are append-only in application code and retained for pinned simulations.
-- The stored R2 keys are internal and never returned by untrusted HTTP routes.
-- Do not seed Magnus/Mortarion listings until their actual decklists are imported,
-- hashed, and read back from R2. There are NO fake public snapshot records.
