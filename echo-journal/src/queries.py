SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS journal_entries(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_prompt TEXT,
    ai_response TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

INSERT_ENTRY = """
INSERT INTO journal_entries (user_prompt, ai_response) 
VALUES (?, ?);
"""

SELECT_ALL_ENTRIES = """
SELECT * FROM journal_entries 
ORDER BY created_at DESC;
"""