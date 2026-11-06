-- PROTOTYPE schema only: requires new isolated D1 database, no existing migrations.
-- Personal decks and public snapshots are different objects.
-- Store personal deck contents in private R2/D1, never in GitHub Pages assets.
CREATE TABLE IF NOT EXISTS decks (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  label TEXT NOT NULL,
  private_content_key TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_decks_owner ON decks(owner_id);

-- A publication has a stable listing identity; its content revisions are immutable.
-- No direct public/private toggle on personal deck records.
CREATE TABLE IF NOT EXISTS publications (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  source_deck_id TEXT,
  label TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'listed' CHECK (status IN ('listed', 'unlisted')),
  current_revision_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_publications_listed ON publications(status);

CREATE TABLE IF NOT EXISTS publication_revisions (
  id TEXT PRIMARY KEY,
  publication_id TEXT NOT NULL REFERENCES publications(id),
  revision_no INTEGER NOT NULL CHECK (revision_no > 0),
  content_sha256 TEXT NOT NULL CHECK (length(content_sha256) = 64),
  immutable_content_key TEXT NOT NULL,
  source_deck_revision TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(publication_id, revision_no)
);
-- No UPDATE or DELETE of publication_revisions in application code.
-- Simulation evidence stores publication_revision_id plus content_sha256 and
-- stays valid even when the listing is unlisted or replaced.
-- Initial Magnus/Mortarion public snapshots MUST be created only after importing
-- their actual source content, recording hashes, and verifying R2 readbacks.
-- Do not insert metadata-only placeholder publications as if they were snapshots.
