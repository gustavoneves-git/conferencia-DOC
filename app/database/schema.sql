CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  original_filename TEXT NOT NULL,
  stored_filename TEXT NOT NULL,
  original_path TEXT NOT NULL,
  document_type TEXT,
  company_name TEXT,
  status TEXT NOT NULL DEFAULT 'UPLOADED',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_pages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  page_number INTEGER NOT NULL,
  extracted_text TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS review_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  total_issues INTEGER NOT NULL DEFAULT 0,
  total_low INTEGER NOT NULL DEFAULT 0,
  total_medium INTEGER NOT NULL DEFAULT 0,
  total_high INTEGER NOT NULL DEFAULT 0,
  total_critical INTEGER NOT NULL DEFAULT 0,
  total_check INTEGER NOT NULL DEFAULT 0,
  ai_mode TEXT,
  model_used TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT,
  FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS review_issues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  review_session_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  page_number INTEGER,
  original_text TEXT,
  issue_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  explanation TEXT,
  technical_reason TEXT,
  suggestion TEXT,
  recommended_action TEXT,
  can_be_highlighted INTEGER NOT NULL DEFAULT 1,
  located_in_pdf INTEGER NOT NULL DEFAULT 0,
  source TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'OPEN',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(review_session_id) REFERENCES review_sessions(id)
);

CREATE TABLE IF NOT EXISTS generated_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_id INTEGER NOT NULL,
  review_session_id INTEGER,
  file_type TEXT NOT NULL,
  path TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(document_id) REFERENCES documents(id),
  FOREIGN KEY(review_session_id) REFERENCES review_sessions(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL,
  entity_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  description TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
