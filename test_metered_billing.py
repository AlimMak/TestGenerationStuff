import pytest
import target


# ---------- overage_charge ----------

def test_overage_zero_units():
    assert target.overage_charge(0) == 0.0


def test_overage_negative_units_raises():
    with pytest.raises(target.BillingError):
        target.overage_charge(-1)


def test_overage_within_first_tier():
    assert target.overage_charge(500) == 5.0


def test_overage_at_first_tier_boundary():
    assert target.overage_charge(1000) == 10.0


def test_overage_single_unit():
    assert target.overage_charge(1) == 0.01


def test_overage_spans_first_and_second_tier():
    assert target.overage_charge(1500) == 14.0


def test_overage_at_second_tier_boundary():
    assert target.overage_charge(10000) == 82.0


def test_overage_spans_all_three_tiers():
    assert target.overage_charge(15000) == 107.0


def test_overage_large_units_uses_final_tier():
    # 100000 units: 1000*0.01 + 9000*0.008 + 90000*0.005
    expected = round(1000 * 0.01 + 9000 * 0.008 + 90000 * 0.005, 2)
    assert target.overage_charge(100000) == expected


def test_overage_custom_tiers():
    custom_tiers = [(100, 0.1), (None, 0.05)]
    # 50 units at 0.1 => 5.0
    assert target.overage_charge(50, tiers=custom_tiers) == 5.0
    # 100 units exactly at boundary => 10.0
    assert target.overage_charge(100, tiers=custom_tiers) == 10.0
    # 150 units: 100*0.1 + 50*0.05 = 10 + 2.5 = 12.5
    assert target.overage_charge(150, tiers=custom_tiers) == 12.5


def test_overage_custom_tiers_single_final_tier_only():
    custom_tiers = [(None, 0.02)]
    assert target.overage_charge(200, tiers=custom_tiers) == 4.0


# ---------- prorate ----------

def test_prorate_half_month():
    assert target.prorate(100.0, 15, 30) == 50.0


def test_prorate_full_month():
    assert target.prorate(100.0, 30, 30) == 100.0


def test_prorate_zero_days_used():
    assert target.prorate(100.0, 0, 30) == 0.0


def test_prorate_days_used_exceeds_days_in_month_is_capped():
    assert target.prorate(100.0, 40, 30) == 100.0


def test_prorate_negative_days_used_raises():
    with pytest.raises(target.BillingError):
        target.prorate(100.0, -1, 30)


def test_prorate_zero_days_in_month_raises():
    with pytest.raises(target.BillingError):
        target.prorate(100.0, 5, 0)


def test_prorate_negative_days_in_month_raises():
    with pytest.raises(target.BillingError):
        target.prorate(100.0, 5, -10)


def test_prorate_rounding():
    # 100 * 10 / 30 = 33.333... -> rounds to 33.33
    assert target.prorate(100.0, 10, 30) == 33.33


def test_prorate_zero_amount():
    assert target.prorate(0.0, 15, 30) == 0.0


# ---------- monthly_bill ----------

def test_monthly_bill_basic():
    # overage_charge(500) = 5.0, gross = 10 + 5 = 15.0, prorate(15,15,30) = 7.5
    assert target.monthly_bill(10.0, 500, 15, 30) == 7.5


def test_monthly_bill_default_days_in_month():
    # days_in_month defaults to 30
    assert target.monthly_bill(10.0, 500, 30) == 15.0


def test_monthly_bill_zero_units():
    assert target.monthly_bill(20.0, 0, 30, 30) == 20.0


def test_monthly_bill_negative_base_fee_raises():
    with pytest.raises(target.BillingError):
        target.monthly_bill(-5.0, 100, 10, 30)


def test_monthly_bill_negative_units_raises():
    with pytest.raises(target.BillingError):
        target.monthly_bill(10.0, -100, 10, 30)


def test_monthly_bill_negative_days_used_raises():
    with pytest.raises(target.BillingError):
        target.monthly_bill(10.0, 100, -1, 30)


def test_monthly_bill_zero_days_in_month_raises():
    with pytest.raises(target.BillingError):
        target.monthly_bill(10.0, 100, 5, 0)


def test_monthly_bill_days_used_capped():
    # days_used > days_in_month should be capped to full month value
    full_bill = target.monthly_bill(10.0, 500, 30, 30)
    capped_bill = target.monthly_bill(10.0, 500, 45, 30)
    assert full_bill == capped_bill


def test_monthly_bill_custom_tiers():
    custom_tiers = [(100, 0.1), (None, 0.05)]
    # overage_charge(150, custom_tiers) = 12.5, gross = 5 + 12.5 = 17.5
    # prorate(17.5, 30, 30) = 17.5
    assert target.monthly_bill(5.0, 150, 30, 30, tiers=custom_tiers) == 17.5