import pytest
import target


def test_add_positive():
    assert target.add(2, 3) == 5


def test_add_negative():
    assert target.add(-2, -3) == -5


def test_add_mixed_sign():
    assert target.add(-2, 3) == 1


def test_add_zero():
    assert target.add(0, 0) == 0


def test_add_floats():
    assert target.add(1.5, 2.5) == 4.0


def test_divide_normal():
    assert target.divide(10, 2) == 5


def test_divide_negative():
    assert target.divide(-10, 2) == -5


def test_divide_floats():
    assert target.divide(5, 2) == 2.5


def test_divide_zero_numerator():
    assert target.divide(0, 5) == 0


def test_divide_by_zero_raises():
    with pytest.raises(ValueError, match="cannot divide by zero"):
        target.divide(10, 0)


def test_clamp_within_range():
    assert target.clamp(5, 0, 10) == 5


def test_clamp_below_range():
    assert target.clamp(-5, 0, 10) == 0


def test_clamp_above_range():
    assert target.clamp(15, 0, 10) == 10


def test_clamp_equal_lo_hi():
    assert target.clamp(5, 3, 3) == 3


def test_clamp_boundary_lo():
    assert target.clamp(0, 0, 10) == 0


def test_clamp_boundary_hi():
    assert target.clamp(10, 0, 10) == 10


def test_clamp_invalid_range_raises():
    with pytest.raises(ValueError, match="lo must be <= hi"):
        target.clamp(5, 10, 0)