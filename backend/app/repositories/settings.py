import sqlite3

from app.config import DEFAULT_PEAK_FACTOR


def get_map(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}


def peak_factor_row(conn: sqlite3.Connection) -> tuple[float, str | None]:
    """当前生效系数及其 settings 更新时间戳。"""
    row = conn.execute("SELECT value, updated_at FROM settings WHERE key='peak_factor'").fetchone()
    if not row:
        return DEFAULT_PEAK_FACTOR, None
    return float(row["value"]), row["updated_at"]


def peak_factor(conn: sqlite3.Connection) -> float:
    return peak_factor_row(conn)[0]


def set_peak_factor(conn: sqlite3.Connection, value: float, changed_at: str) -> None:
    conn.execute(
        "UPDATE settings SET value=?, updated_at=? WHERE key='peak_factor'",
        (str(value), changed_at),
    )
