import sqlite3
from datetime import datetime, timezone


def insert(
    conn: sqlite3.Connection,
    old_value: float,
    new_value: float,
    operator: str,
    note: str | None,
    changed_at: str | None = None,
) -> int:
    changed_at = changed_at or datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """
        INSERT INTO peak_factor_audits(old_value, new_value, changed_at, operator, note)
        VALUES (?,?,?,?,?)
        """,
        (old_value, new_value, changed_at, operator, note),
    )
    return int(cur.lastrowid)


def list_page(conn: sqlite3.Connection, page: int = 1, page_size: int = 10) -> dict:
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    total = conn.execute("SELECT COUNT(*) c FROM peak_factor_audits").fetchone()["c"]
    rows = conn.execute(
        """
        SELECT id, old_value, new_value, changed_at, operator, note
        FROM peak_factor_audits
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        (page_size, (page - 1) * page_size),
    ).fetchall()
    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
