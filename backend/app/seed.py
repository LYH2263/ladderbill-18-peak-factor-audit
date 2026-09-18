import json
from datetime import datetime, timezone

from app.db import connect
from app.engines.peak_compare import compare_plain_vs_peak
from app.engines.tier_progressive import calc_bill


def init_db():
    conn = connect()
    conn.executescript(
        """
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS accounts(
        id INTEGER PRIMARY KEY, name TEXT, meter_no TEXT, note TEXT);
    CREATE TABLE IF NOT EXISTS readings(id INTEGER PRIMARY KEY, account_id INTEGER, kwh REAL, peak INTEGER);
    CREATE TABLE IF NOT EXISTS tiers(id INTEGER PRIMARY KEY, up_to REAL, price REAL, sort_order INTEGER);
    CREATE TABLE IF NOT EXISTS calc_runs(
        id INTEGER PRIMARY KEY,
        kind TEXT,
        account_id INTEGER,
        input_json TEXT,
        result_json TEXT,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS peak_factor_audits(
        id INTEGER PRIMARY KEY,
        old_value REAL NOT NULL,
        new_value REAL NOT NULL,
        changed_at TEXT NOT NULL,
        operator TEXT NOT NULL,
        remark TEXT
    );
    """
    )
    # 迁移：老库的 settings 表没有 updated_at 列
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(settings)").fetchall()}
    if "updated_at" not in cols:
        conn.execute("ALTER TABLE settings ADD COLUMN updated_at TEXT")
    if conn.execute("SELECT COUNT(*) c FROM accounts").fetchone()["c"] == 0:
        conn.execute(
            "INSERT INTO accounts(name, meter_no, note) VALUES ('张家', 'M-1001', '对照：正常用量')"
        )
        conn.execute(
            "INSERT INTO accounts(name, meter_no, note) VALUES ('李家(种子偏高)', 'M-1002', '对照：高用量+尖峰')"
        )
        conn.executemany(
            "INSERT INTO tiers(up_to, price, sort_order) VALUES (?,?,?)",
            [(180, 0.52, 1), (260, 0.62, 2), (None, 0.82, 3)],
        )
        conn.execute("INSERT INTO readings(account_id, kwh, peak) VALUES (1, 120, 0)")
        conn.execute("INSERT INTO readings(account_id, kwh, peak) VALUES (2, 400, 1)")
        conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES ('peak_factor', '1.2')")
        conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES ('currency', 'CNY')")
        tiers = [{"up_to": r[0], "price": r[1]} for r in [(180, 0.52), (260, 0.62), (None, 0.82)]]
        bill1 = calc_bill(120, tiers, 1.0)
        conn.execute(
            "INSERT INTO calc_runs(kind, account_id, input_json, result_json, created_at) VALUES (?,?,?,?,datetime('now'))",
            ("bill", 1, json.dumps({"kwh": 120, "peak": False}), json.dumps(bill1, ensure_ascii=False)),
        )
        cmp2 = compare_plain_vs_peak(400, tiers, 1.2)
        conn.execute(
            "INSERT INTO calc_runs(kind, account_id, input_json, result_json, created_at) VALUES (?,?,?,?,datetime('now'))",
            ("compare", 2, json.dumps({"kwh": 400}), json.dumps(cmp2, ensure_ascii=False)),
        )
    # 回填：新建或迁移后仍没有时间戳的 settings 行统一补上
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE settings SET updated_at = ? WHERE updated_at IS NULL", (now,))
    conn.commit()
    conn.close()
