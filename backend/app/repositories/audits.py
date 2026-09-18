import sqlite3


def insert(
    conn: sqlite3.Connection,
    old_value: float,
    new_value: float,
    operator: str,
    remark: str | None,
    changed_at: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO peak_factor_audits(old_value, new_value, changed_at, operator, remark)
        VALUES (?,?,?,?,?)
        """,
        (old_value, new_value, changed_at, operator, remark),
    )
    return int(cur.lastrowid)


def list_page(conn: sqlite3.Connection, page: int, page_size: int) -> dict:
    total = conn.execute("SELECT COUNT(*) c FROM peak_factor_audits").fetchone()["c"]
    rows = conn.execute(
        """
        SELECT id, old_value, new_value, changed_at, operator, remark
        FROM peak_factor_audits ORDER BY id DESC LIMIT ? OFFSET ?
        """,
        (page_size, (page - 1) * page_size),
    ).fetchall()
    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
