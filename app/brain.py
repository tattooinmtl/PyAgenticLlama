"""
Persistent memory using SQLite. Uses simple LIKE search — reliable and fast enough
for personal-scale memory (thousands of records). No FTS triggers needed.
"""
import sqlite3, json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'brain.db'
DB_PATH.parent.mkdir(exist_ok=True)

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _conn() as c:
        c.executescript('''
            CREATE TABLE IF NOT EXISTS memories (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                type    TEXT NOT NULL DEFAULT 'fact',
                content TEXT NOT NULL,
                tags    TEXT DEFAULT '[]',
                project TEXT DEFAULT '',
                ts      REAL DEFAULT (unixepoch())
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                model       TEXT DEFAULT '',
                personality TEXT DEFAULT 'default',
                ts          REAL DEFAULT (unixepoch())
            );

            CREATE TABLE IF NOT EXISTS messages (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                conv_id TEXT NOT NULL,
                role    TEXT NOT NULL,
                content TEXT NOT NULL,
                ts      REAL DEFAULT (unixepoch())
            );

            CREATE INDEX IF NOT EXISTS idx_memories_ts      ON memories(ts DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_conv    ON messages(conv_id);
            CREATE INDEX IF NOT EXISTS idx_conversations_ts ON conversations(ts DESC);
        ''')

# ── Memory ────────────────────────────────────────────────────────

def remember(content: str, type_: str = 'fact', tags: list | None = None, project: str = '') -> int:
    with _conn() as c:
        cur = c.execute(
            'INSERT INTO memories (type, content, tags, project) VALUES (?,?,?,?)',
            (type_, content, json.dumps(tags or []), project)
        )
        return cur.lastrowid

def recall(query: str, limit: int = 10) -> list[dict]:
    words = query.strip().split()
    if not words:
        return all_memories(limit)
    with _conn() as c:
        # Match any row that contains ALL words (AND logic)
        conditions = ' AND '.join(['(content LIKE ? OR tags LIKE ?)'] * len(words))
        params = []
        for w in words:
            params += [f'%{w}%', f'%{w}%']
        params.append(limit)
        rows = c.execute(
            f'SELECT * FROM memories WHERE {conditions} ORDER BY ts DESC LIMIT ?',
            params
        ).fetchall()
    return [dict(r) for r in rows]

def all_memories(limit: int = 100) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            'SELECT * FROM memories ORDER BY ts DESC LIMIT ?', (limit,)
        ).fetchall()
    return [dict(r) for r in rows]

def delete_memory(id_: int):
    with _conn() as c:
        c.execute('DELETE FROM memories WHERE id=?', (id_,))

def clear_memories(project: str = ''):
    with _conn() as c:
        if project:
            c.execute('DELETE FROM memories WHERE project=?', (project,))
        else:
            c.execute('DELETE FROM memories')

# ── Conversations ─────────────────────────────────────────────────

def save_conversation(id_: str, title: str, model: str = '', personality: str = 'default'):
    with _conn() as c:
        c.execute(
            'INSERT OR REPLACE INTO conversations (id, title, model, personality) VALUES (?,?,?,?)',
            (id_, title, model, personality)
        )

def add_message(conv_id: str, role: str, content: str):
    with _conn() as c:
        c.execute(
            'INSERT INTO messages (conv_id, role, content) VALUES (?,?,?)',
            (conv_id, role, content)
        )

def list_conversations(limit: int = 50) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            'SELECT * FROM conversations ORDER BY ts DESC LIMIT ?', (limit,)
        ).fetchall()
    return [dict(r) for r in rows]

def get_conversation_messages(conv_id: str) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            'SELECT * FROM messages WHERE conv_id=? ORDER BY ts', (conv_id,)
        ).fetchall()
    return [dict(r) for r in rows]

def delete_conversation(conv_id: str):
    with _conn() as c:
        c.execute('DELETE FROM messages WHERE conv_id=?', (conv_id,))
        c.execute('DELETE FROM conversations WHERE id=?', (conv_id,))

init_db()
