import sqlite3

from app.config import DEFAULT_PEAK_FACTOR

PEAK_FACTOR_KEY = "peak_factor"


def get_map(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}


def peak_factor(conn: sqlite3.Connection) -> float:
    return peak_factor_row(conn)[0]


def peak_factor_row(conn: sqlite3.Connection) -> tuple[float, str | None]:
    """返回 (当前生效系数, settings 行的更新时间戳)。"""
    row = conn.execute(
        "SELECT value, updated_at FROM settings WHERE key=?", (PEAK_FACTOR_KEY,)
    ).fetchone()
    if not row:
        return DEFAULT_PEAK_FACTOR, None
    return float(row["value"]), row["updated_at"]


def update_peak_factor(conn: sqlite3.Connection, value: float, updated_at: str) -> None:
    conn.execute(
        "UPDATE settings SET value=?, updated_at=? WHERE key=?",
        (str(value), updated_at, PEAK_FACTOR_KEY),
    )
