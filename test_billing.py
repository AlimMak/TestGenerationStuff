import pytest
import target
from target import (
    BillingError,
    Coupon,
    line_total,
    coupon_discount,
    tax,
    checkout,
)


# ---------- line_total ----------

def test_line_total_normal():
    assert line_total(2, 3.5) == 7.0


def test_line_total_zero_quantity():
    assert line_total(0, 5.0) == 0.0


def test_line_total_zero_price():
    assert line_total(3, 0.0) == 0.0


def test_line_total_rounding():
    assert line_total(3, 0.333) == 1.0


def test_line_total_negative_quantity_raises():
    with pytest.raises(BillingError):
        line_total(-1, 5.0)


def test_line_total_negative_price_raises():
    with pytest.raises(BillingError):
        line_total(1, -5.0)


# ---------- coupon_discount ----------

def test_coupon_discount_none_coupon():
    assert coupon_discount(100.0, None) == 0.0


def test_coupon_discount_negative_subtotal_raises():
    with pytest.raises(BillingError):
        coupon_discount(-10.0, None)


def test_coupon_discount_below_min_spend():
    coupon = Coupon(kind="fixed", value=10.0, min_spend=50.0)
    assert coupon_discount(20.0, coupon) == 0.0


def test_coupon_discount_percent_basic():
    coupon = Coupon(kind="percent", value=10.0)
    assert coupon_discount(100.0, coupon) == 10.0


def test_coupon_discount_percent_zero():
    coupon = Coupon(kind="percent", value=0.0)
    assert coupon_discount(100.0, coupon) == 0.0


def test_coupon_discount_percent_hundred():
    coupon = Coupon(kind="percent", value=100.0)
    assert coupon_discount(50.0, coupon) == 50.0


def test_coupon_discount_percent_out_of_range_low():
    coupon = Coupon(kind="percent", value=-1.0)
    with pytest.raises(BillingError):
        coupon_discount(100.0, coupon)


def test_coupon_discount_percent_out_of_range_high():
    coupon = Coupon(kind="percent", value=101.0)
    with pytest.raises(BillingError):
        coupon_discount(100.0, coupon)


def test_coupon_discount_fixed_basic():
    coupon = Coupon(kind="fixed", value=15.0)
    assert coupon_discount(100.0, coupon) == 15.0


def test_coupon_discount_fixed_negative_raises():
    coupon = Coupon(kind="fixed", value=-5.0)
    with pytest.raises(BillingError):
        coupon_discount(100.0, coupon)


def test_coupon_discount_fixed_exceeds_subtotal_capped():
    coupon = Coupon(kind="fixed", value=150.0)
    assert coupon_discount(100.0, coupon) == 100.0


def test_coupon_discount_unknown_kind_raises():
    coupon = Coupon(kind="mystery", value=10.0)
    with pytest.raises(BillingError):
        coupon_discount(100.0, coupon)


def test_coupon_discount_max_discount_cap():
    coupon = Coupon(kind="percent", value=50.0, max_discount=10.0)
    assert coupon_discount(100.0, coupon) == 10.0


def test_coupon_discount_max_discount_not_reached():
    coupon = Coupon(kind="percent", value=10.0, max_discount=50.0)
    assert coupon_discount(100.0, coupon) == 10.0


def test_coupon_discount_min_spend_exact_boundary():
    coupon = Coupon(kind="fixed", value=5.0, min_spend=50.0)
    assert coupon_discount(50.0, coupon) == 5.0


def test_coupon_discount_rounding():
    coupon = Coupon(kind="percent", value=33.333)
    result = coupon_discount(10.0, coupon)
    assert result == round(10.0 * 33.333 / 100, 2)


# ---------- tax ----------

def test_tax_basic():
    assert tax(100.0, 0.1) == 10.0


def test_tax_zero_rate():
    assert tax(100.0, 0.0) == 0.0


def test_tax_full_rate():
    assert tax(100.0, 1.0) == 100.0


def test_tax_zero_amount():
    assert tax(0.0, 0.5) == 0.0


def test_tax_negative_amount_raises():
    with pytest.raises(BillingError):
        tax(-10.0, 0.1)


def test_tax_rate_below_zero_raises():
    with pytest.raises(BillingError):
        tax(100.0, -0.1)


def test_tax_rate_above_one_raises():
    with pytest.raises(BillingError):
        tax(100.0, 1.1)


def test_tax_rounding():
    assert tax(10.0, 0.333) == round(10.0 * 0.333, 2)


# ---------- checkout ----------

def test_checkout_empty_cart_raises():
    with pytest.raises(BillingError):
        checkout([])


def test_checkout_basic_no_coupon_no_tax():
    items = [(2, 10.0), (1, 5.0)]
    result = checkout(items)
    assert result == {
        "subtotal": 25.0,
        "discount": 0.0,
        "tax": 0.0,
        "total": 25.0,
    }


def test_checkout_with_percent_coupon():
    items = [(1, 100.0)]
    coupon = Coupon(kind="percent", value=10.0)
    result = checkout(items, coupon=coupon)
    assert result["subtotal"] == 100.0
    assert result["discount"] == 10.0
    assert result["tax"] == 0.0
    assert result["total"] == 90.0


def test_checkout_with_fixed_coupon_and_tax():
    items = [(1, 100.0)]
    coupon = Coupon(kind="fixed", value=20.0)
    result = checkout(items, coupon=coupon, tax_rate=0.1)
    assert result["subtotal"] == 100.0
    assert result["discount"] == 20.0
    assert result["tax"] == 8.0
    assert result["total"] == 88.0


def test_checkout_with_tax_only():
    items = [(1, 50.0)]
    result = checkout(items, tax_rate=0.2)
    assert result["subtotal"] == 50.0
    assert result["discount"] == 0.0
    assert result["tax"] == 10.0
    assert result["total"] == 60.0


def test_checkout_propagates_line_total_error():
    with pytest.raises(BillingError):
        checkout([(-1, 10.0)])


def test_checkout_propagates_coupon_error():
    items = [(1, 100.0)]
    coupon = Coupon(kind="percent", value=150.0)
    with pytest.raises(BillingError):
        checkout(items, coupon=coupon)


def test_checkout_propagates_tax_error():
    items = [(1, 100.0)]
    with pytest.raises(BillingError):
        checkout(items, tax_rate=1.5)


def test_checkout_multiple_items_with_coupon_max_discount():
    items = [(2, 50.0), (1, 25.0)]  # subtotal 125.0
    coupon = Coupon(kind="percent", value=20.0, max_discount=15.0)
    result = checkout(items, coupon=coupon)
    assert result["subtotal"] == 125.0
    assert result["discount"] == 15.0
    assert result["total"] == round(125.0 - 15.0, 2)


def test_checkout_coupon_below_min_spend_no_discount():
    items = [(1, 10.0)]
    coupon = Coupon(kind="fixed", value=5.0, min_spend=100.0)
    result = checkout(items, coupon=coupon)
    assert result["discount"] == 0.0
    assert result["total"] == 10.0