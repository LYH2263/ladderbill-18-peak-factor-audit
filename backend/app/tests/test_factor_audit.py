import pytest

from app.services.billing_service import BillingService, SameFactorError


def test_initial_peak_factor_state(fresh_db):
    with BillingService() as svc:
        state = svc.peak_factor_state()
    assert state["peak_factor"] == 1.2
    assert state["coefficient_as_of"]  # settings 行带时间戳


def test_change_writes_audit_and_updates_settings(fresh_db):
    with BillingService() as svc:
        audit = svc.change_peak_factor(1.35, "zhang", "夏季调整")
        state = svc.peak_factor_state()
        page = svc.list_factor_audits()
    assert audit["old_value"] == 1.2
    assert audit["new_value"] == 1.35
    assert audit["operator"] == "zhang"
    assert audit["note"] == "夏季调整"
    assert audit["changed_at"]
    assert state["peak_factor"] == 1.35
    assert state["coefficient_as_of"] == audit["changed_at"]
    assert page["total"] == 1
    assert page["items"][0]["old_value"] == 1.2


def test_same_value_is_rejected(fresh_db):
    with BillingService() as svc:
        with pytest.raises(SameFactorError):
            svc.change_peak_factor(1.2, "zhang", None)
        # 拒绝写入：settings 未动、审计表为空
        assert svc.peak_factor_state()["peak_factor"] == 1.2
        assert svc.list_factor_audits()["total"] == 0


def test_audit_pagination(fresh_db):
    with BillingService() as svc:
        for i in range(12):
            svc.change_peak_factor(1.2 + (i + 1) * 0.01, "op", None)
        p1 = svc.list_factor_audits(page=1, page_size=10)
        p2 = svc.list_factor_audits(page=2, page_size=10)
    assert p1["total"] == 12
    assert p1["page"] == 1
    assert len(p1["items"]) == 10
    assert len(p2["items"]) == 2
    # 最新条目排在最前
    assert p1["items"][0]["new_value"] > p1["items"][-1]["new_value"]


def test_bill_and_compare_carry_coefficient_as_of(fresh_db):
    with BillingService() as svc:
        bill = svc.run_bill(220, False, None, False)
        compare = svc.run_compare(400, False)
    assert bill["coefficient"] == 1.2
    assert bill["coefficient_as_of"]
    assert compare["coefficient"] == 1.2
    assert compare["coefficient_as_of"]
