"""Test the general utilities."""

import pytest

from okrs_api.utils import minmax, lower_keys


@pytest.mark.parametrize(
    "number, minimum, maximum, expected",
    [
        pytest.param(150, 20, 120, 120, id="outside-max-range"),
        pytest.param(50, 20, 120, 50, id="inside-range"),
        pytest.param(-50, 20, 120, 20, id="outside-min-range"),
    ],
)
def test_minmax(number, minimum, maximum, expected):
    """Ensure any number passed is in clipped at minumum or maximum."""
    assert minmax(number, minimum, maximum) == expected


def test_minmax_defaults():
    """Ensure any number passed is in clipped at minumum or maximum defaults."""
    assert minmax(130) == 100
    assert minmax(50) == 50
    assert minmax(-50) == 0


@pytest.mark.parametrize(
    "original, expected",
    [
        pytest.param({"a-1": "dog"}, {"a-1": "dog"}),
        pytest.param(
            {"PeT": "dog", "LICENSE": {"ID": "11", "OWNER": "LISA"}},
            {"pet": "dog", "license": {"id": "11", "owner": "LISA"}},
        ),
    ],
)
def test_lower_keys(original, expected):
    """Ensure that a dictionary will have all its keys lowered."""
    assert lower_keys(original) == expected
