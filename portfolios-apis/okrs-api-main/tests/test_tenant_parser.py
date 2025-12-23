import pytest

from okrs_api.tenant_parser import TenantParser


@pytest.mark.parametrize(
    "tenant_id_str, expected_app, expected_env, expected_id",
    [
        pytest.param(
            "PROJECTPLACE~pp-333334444",
            "PROJECTPLACE",
            "pp",
            "333334444",
            id="project-place-sample",
        ),
        pytest.param(
            "SPIGIT~whatev-123456789",
            "SPIGIT",
            "whatev",
            "123456789",
            id="spigit-sample",
        ),
        pytest.param(
            "E1_PRM~p-31mgpdqajn|integ18_e1_lk",
            "E1_PRM",
            "p",
            "31mgpdqajn|integ18_e1_lk",
            id="e1-sample",
        ),
    ],
)
def test_tenant_parser(tenant_id_str, expected_app, expected_env, expected_id):
    """Ensure the TenantParser works properly."""
    parser = TenantParser(tenant_id_str)
    assert parser.tenant_code == tenant_id_str
    assert parser.tenant_app == expected_app
    assert parser.tenant_env == expected_env
    assert parser.tenant_id == expected_id


def test_okrs_tenant_id():
    """Ensure the TenantParser okrs_tenant_id works properly."""
    parser = TenantParser("LEANKIT~D10-12345")
    assert parser.okrs_tenant_id == "okrs-D10-12345"
