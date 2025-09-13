import sqlite3
from pathlib import Path
import sqlite3
from pathlib import Path

dbs = [
    Path('memory_data/ai_memories.db'),
    Path('memory_data/mcp_tool_calls.db')
]

for db in dbs:
    print('\nDB:', db)
    if not db.exists():
        print('  (not found)')
        continue
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # list tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print('  tables:', tables)
    for t in tables:
        try:
            cur.execute(f'SELECT COUNT(*) as c FROM {t}')
            c = cur.fetchone()['c']
        except Exception as e:
            c = f'err: {e}'
        print(f'   {t}: {c}')
        try:
            cur.execute(f'SELECT * FROM {t} ORDER BY rowid DESC LIMIT 3')
            rows = cur.fetchall()
            for r in rows:
                # show a compact sample
                d = dict(r)
                for k in list(d.keys()):
                    if isinstance(d[k], bytes):
                        d[k] = '<bytes>'
                    if isinstance(d[k], str) and len(d[k])>200:
                        d[k] = d[k][:200] + '...'
                print('     ', d)
        except Exception as e:
            print('     sample err:', e)
    conn.close()
