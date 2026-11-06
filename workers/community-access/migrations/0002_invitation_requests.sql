-- Apply to isolated development D1 after 0001.
-- A request is NOT a Cloudflare Access account, identity, approval or allowlist entry.
CREATE TABLE IF NOT EXISTS invitation_requests (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL DEFAULT '',
  note TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK(status IN ('pending','declined','awaiting_access_allowlist','active')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_by TEXT,
  reviewed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_invitation_status ON invitation_requests(status);
