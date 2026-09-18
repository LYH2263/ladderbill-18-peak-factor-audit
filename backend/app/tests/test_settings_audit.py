import sqlite3

import pytest

from app.services.billing_service import BillingService, UnchangedPeakFactorError

DDL = """
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
CREATE TABLE tiers(id INTEGER PRIMARY KEY, up_to REAL, price REAL, sort_order INTEGER);
CREATE TABLE calc_runs(
    id INTEGER PRIMARY KEY, kind TEXT, account_id INTEGER,
    input_json TEXT, result_json TEXT, created_at TEXT);
CREATE TABLE peak_factor_audits(
    id INTEGER PRIMARY KEY, old_value REAL NOT NULL, new_value REAL NOT NULL,
    changed_at TEXT NOT NULL, operator TEXT NOT NULL, remark TEXT);
"""
TIERS = [(180, 0.52, 1), (260, 0.62, 2), (None, 0.82, 3)]
SEEDED_AT = "2026-01-01T00:00:00+00:00"


def _connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


@pytest.fixture()
def svc(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    conn = _connect(db)
    conn.executescript(DDL)
    conn.execute(
        "INSERT INTO settings(key, value, updated_at) VALUES ('peak_factor', '1.2', ?)",
        (SEEDED_AT,),
    )
    conn.executemany("INSERT INTO tiers(up_to, price, sort_order) VALUES (?,?,?)", TIERS)
    conn.commit()
    conn.close()
    monkeypatch.setattr("app.services.billing_service.connect", lambda: _connect(db))
    with BillingService() as s:
        yield s


def test_update_writes_audit_and_settings(svc):
    entry = svc.update_peak_factor(1.5, "admin", "迎峰度夏")
    assert entry["old_value"] == 1.2
    assert entry["new_value"] == 1.5
    assert entry["operator"] == "admin"
    assert entry["remark"] == "迎峰度夏"
    assert entry["changed_at"]

    page = svc.list_peak_factor_audits(page=1, page_size=10)
    assert page["total"] == 1
    assert page["items"][0]["id"] == entry["id"]
    assert page["items"][0]["changed_at"] == entry["changed_at"]
    # 当前生效值仍从 settings 读取，且时间戳与审计一致
    assert svc.settings_map()["peak_factor"] == "1.5"
    assert svc.run_bill(100, peak=True, account_id=None, persist=False)["coefficient_as_of"] == entry["changed_at"]


def test_same_value_rejected(svc):
    with pytest.raises(UnchangedPeakFactorError):
        svc.update_peak_factor(1.2, "admin", None)
    assert svc.list_peak_factor_audits()["total"] == 0
    assert svc.settings_map()["peak_factor"] == "1.2"


def test_same_value_rejected_even_with_different_text(svc):
    # “1.20” 与 “1.2” 数值相同，同样拒绝
    with pytest.raises(UnchangedPeakFactorError):
        svc.update_peak_factor(1.20, "admin", "只是换个写法")


def test_audit_pagination(svc):
    svc.update_peak_factor(1.3, "admin", None)
    svc.update_peak_factor(1.4, "admin", None)
    svc.update_peak_factor(1.5, "admin", None)

    page1 = svc.list_peak_factor_audits(page=1, page_size=2)
    page2 = svc.list_peak_factor_audits(page=2, page_size=2)
    assert page1["total"] == 3
    assert [i["new_value"] for i in page1["items"]] == [1.5, 1.4]  # 最新在前
    assert [i["new_value"] for i in page2["items"]] == [1.3]


def test_coefficient_as_of_tracks_settings_update(svc):
    r = svc.run_bill(100, peak=True, account_id=None, persist=False)
    assert r["coefficient_as_of"] == SEEDED_AT
    entry = svc.update_peak_factor(1.6, "admin", None)
    r2 = svc.run_bill(100, peak=True, account_id=None, persist=False)
    assert r2["coefficient_as_of"] == entry["changed_at"]
    r3 = svc.run_compare(100, persist=False)
    assert r3["coefficient_as_of"] == entry["changed_at"]
