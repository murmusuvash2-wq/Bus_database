import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/bus.db")

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT,
            bus_name TEXT,
            operator_type TEXT,
            operator_name TEXT,
            source_city TEXT,
            destination_city TEXT,
            departure_time TEXT,
            arrival_time TEXT,
            route TEXT,
            stoppages TEXT,
            bus_type TEXT,
            frequency TEXT,
            source TEXT,
            last_updated TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON buses(source_city)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_dest ON buses(destination_city)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON buses(state)")
    conn.commit()
    conn.close()

def upsert_buses(rows):
    """rows = list of dicts"""
    if not rows:
        return 0
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    count = 0
    for r in rows:
        conn.execute("""
            INSERT INTO buses (
                state, bus_name, operator_type, operator_name,
                source_city, destination_city, departure_time, arrival_time,
                route, stoppages, bus_type, frequency, source, last_updated
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r.get("state"),
            r.get("bus_name"),
            r.get("operator_type", "Unknown"),
            r.get("operator_name"),
            r.get("source_city"),
            r.get("destination_city"),
            r.get("departure_time"),
            r.get("arrival_time"),
            r.get("route"),
            json.dumps(r.get("stoppages") or []),
            r.get("bus_type"),
            r.get("frequency"),
            r.get("source", "unknown"),
            now
        ))
        count += 1
    conn.commit()
    conn.close()
    return count

def export_json(path="export/buses.json"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    rows = conn.execute("SELECT * FROM buses ORDER BY source_city, departure_time").fetchall()
    conn.close()
    data = []
    for r in rows:
        item = dict(r)
        try:
            item["stoppages"] = json.loads(item["stoppages"] or "[]")
        except Exception:
            item["stoppages"] = []
        data.append(item)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return len(data)

def clear_source(source_name):
    conn = get_conn()
    conn.execute("DELETE FROM buses WHERE source = ?", (source_name,))
    conn.commit()
    conn.close()
