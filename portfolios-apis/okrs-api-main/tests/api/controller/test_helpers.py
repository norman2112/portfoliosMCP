from okrs_api.api.controller.helpers import sanitise_product_type


def test_sanitise_leankit():
    """Test whether we properly sanitise the product type for leankit."""

    assert sanitise_product_type("leankit") == "leankit"


def test_sanitise_e1_prm():
    """Test whether we properly sanitise the product type for portfolios."""

    assert sanitise_product_type("e1_prm") == "e1_prm"


def test_sanitise_e1():
    """Test whether we properly sanitise the product type for portfolios."""

    assert sanitise_product_type("e1") == "e1_prm"


def test_sanitise_e1_caps():
    """Test whether we properly sanitise the product type for portfolios."""

    assert sanitise_product_type("E1") == "e1_prm"


def test_sanitise_leankit_caps():
    """Test whether we properly sanitise the product type for leankit."""

    assert sanitise_product_type("LEANKIT") == "leankit"


def test_sanitise_bogus():
    """Test whether we properly sanitise the product type for leankit."""

    assert sanitise_product_type(123) == "123"
