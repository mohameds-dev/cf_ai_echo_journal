SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS journal_entries(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_prompt TEXT,
    ai_response TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY, 
    value TEXT
);
"""

INSERT_ENTRY = """
INSERT INTO journal_entries (user_prompt, ai_response) 
VALUES (?, ?);
"""

SELECT_ALL_ENTRIES = """
SELECT 
    id, 
    user_prompt, 
    ai_response, 
    created_at 
FROM history 
ORDER BY created_at DESC;
"""

RETRIEVE_CONTEXT = """
SELECT value FROM state WHERE key = 'context' LIMIT 1
"""

UDPATE_CONTEXT = """
INSERT OR REPLACE INTO state (key, value) VALUES ('context', ?)
"""

CLEAR_HISTORY = "DELETE FROM journal_entries;"
CLEAR_CONTEXT = "DELETE FROM state WHERE key = 'context';"