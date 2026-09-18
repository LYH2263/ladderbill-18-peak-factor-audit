from datetime import datetime, timezone

from app.db import connect
from app.engines.peak_compare import compare_plain_vs_peak
from app.engines.tier_progressive import calc_bill
from app.repositories import accounts as accounts_repo
from app.repositories import factor_audits as factor_audits_repo
from app.repositories import readings as readings_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import tiers as tiers_repo


class SameFactorError(ValueError):
    """新值与当前生效值相同时拒绝写入。"""


class BillingService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def list_accounts(self):
        return accounts_repo.list_all(self._conn)

    def get_account(self, account_id: int):
        return accounts_repo.get(self._conn, account_id)

    def list_tiers(self):
        return tiers_repo.list_ordered(self._conn)

    def list_readings(self):
        return readings_repo.list_all(self._conn)

    def readings_for_account(self, account_id: int):
        return readings_repo.for_account(self._conn, account_id)

    def settings_map(self):
        return settings_repo.get_map(self._conn)

    def peak_factor_state(self) -> dict:
        value, as_of = settings_repo.peak_factor_row(self._conn)
        return {"peak_factor": value, "coefficient_as_of": as_of}

    def change_peak_factor(self, new_value: float, operator: str, note: str | None) -> dict:
        old_value, _ = settings_repo.peak_factor_row(self._conn)
        new_value = float(new_value)
        if new_value == old_value:
            raise SameFactorError(f"新值与当前生效值相同：{old_value}")
        now = datetime.now(timezone.utc).isoformat()
        try:
            settings_repo.update_peak_factor(self._conn, new_value, now)
            audit_id = factor_audits_repo.insert(
                self._conn, old_value, new_value, operator, note, changed_at=now
            )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return {
            "id": audit_id,
            "old_value": old_value,
            "new_value": new_value,
            "changed_at": now,
            "operator": operator,
            "note": note,
        }

    def list_factor_audits(self, page: int = 1, page_size: int = 10) -> dict:
        return factor_audits_repo.list_page(self._conn, page, page_size)

    def run_bill(self, kwh: float, peak: bool, account_id: int | None, persist: bool):
        tiers = tiers_repo.as_calc_rows(self._conn)
        pf, as_of = settings_repo.peak_factor_row(self._conn)
        factor = pf if peak else 1.0
        result = calc_bill(kwh, tiers, factor)
        run_id = None
        if persist:
            run_id = runs_repo.insert(
                self._conn,
                "bill",
                {"kwh": kwh, "peak": peak, "account_id": account_id},
                result,
                account_id,
            )
        return {"run_id": run_id, "coefficient": pf, "coefficient_as_of": as_of, **result}

    def run_compare(self, kwh: float, persist: bool):
        tiers = tiers_repo.as_calc_rows(self._conn)
        pf, as_of = settings_repo.peak_factor_row(self._conn)
        result = compare_plain_vs_peak(kwh, tiers, pf)
        run_id = None
        if persist:
            run_id = runs_repo.insert(self._conn, "compare", {"kwh": kwh}, result, None)
        return {"run_id": run_id, "coefficient": pf, "coefficient_as_of": as_of, **result}

    def list_history(self, limit: int = 50):
        return runs_repo.list_recent(self._conn, limit)

    def get_run(self, run_id: int):
        return runs_repo.get(self._conn, run_id)

    def dashboard_stats(self):
        accounts = accounts_repo.list_all(self._conn)
        readings = readings_repo.list_all(self._conn)
        clean = [a for a in accounts if "种子" not in a.get("name", "")]
        dirty = [a for a in accounts if "种子" in a.get("name", "")]
        return {
            "account_count": len(accounts),
            "reading_count": len(readings),
            "clean_accounts": len(clean),
            "dirty_accounts": len(dirty),
            "recent_runs": len(runs_repo.list_recent(self._conn, 5)),
        }
