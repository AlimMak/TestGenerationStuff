import pytest
import target


class TestMean:
    def test_single_value(self):
        assert target.mean([5.0]) == 5.0

    def test_multiple_values(self):
        assert target.mean([1, 2, 3, 4]) == 2.5

    def test_negative_values(self):
        assert target.mean([-1, -2, -3]) == -2.0

    def test_mixed_sign_values(self):
        assert target.mean([-5, 5]) == 0.0

    def test_floats(self):
        assert target.mean([1.5, 2.5, 3.5]) == pytest.approx(2.5)

    def test_empty_raises(self):
        with pytest.raises(target.StatsError):
            target.mean([])

    def test_empty_raises_is_value_error(self):
        with pytest.raises(ValueError):
            target.mean([])


class TestMedian:
    def test_odd_count(self):
        assert target.median([3, 1, 2]) == 2

    def test_odd_count_single(self):
        assert target.median([42]) == 42

    # SOURCE BUG: median() should average the two middle elements for even counts
    def test_even_count_average(self):
        assert target.median([1, 2, 3, 4]) == 2.5

    # SOURCE BUG: median() should average the two middle elements for even counts
    def test_even_count_unsorted(self):
        assert target.median([4, 1, 3, 2]) == 2.5

    # SOURCE BUG: median() should average the two middle elements for even counts
    def test_even_count_duplicates(self):
        assert target.median([1, 1, 2, 2]) == 1.5

    def test_odd_count_unsorted(self):
        assert target.median([5, 1, 3]) == 3

    def test_negative_values_odd(self):
        assert target.median([-1, -5, -3]) == -3

    # SOURCE BUG: median() should average the two middle elements for even counts
    def test_negative_values_even(self):
        assert target.median([-1, -2, -3, -4]) == -2.5

    def test_empty_raises(self):
        with pytest.raises(target.StatsError):
            target.median([])

    def test_empty_raises_is_value_error(self):
        with pytest.raises(ValueError):
            target.median([])


class TestVariance:
    def test_two_values(self):
        assert target.variance([1, 2]) == pytest.approx(0.5)

    def test_multiple_values(self):
        # values: 2,4,4,4,5,5,7,9 -> sample variance = 4.571428...
        data = [2, 4, 4, 4, 5, 5, 7, 9]
        assert target.variance(data) == pytest.approx(4.571428571428571)

    def test_identical_values_zero_variance(self):
        assert target.variance([3, 3, 3]) == pytest.approx(0.0)

    def test_negative_values(self):
        assert target.variance([-1, -2, -3]) == pytest.approx(1.0)

    def test_single_value_raises(self):
        with pytest.raises(target.StatsError):
            target.variance([1])

    def test_empty_raises(self):
        with pytest.raises(target.StatsError):
            target.variance([])

    def test_error_is_value_error_subclass(self):
        with pytest.raises(ValueError):
            target.variance([])