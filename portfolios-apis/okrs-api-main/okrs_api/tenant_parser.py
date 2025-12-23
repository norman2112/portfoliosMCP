"""Houses the class for the TenantParser."""


class TenantParser:
    """
    All break-out logic for parsing a `tenant_id_str`.

    tenant_id_str is in the format of:
    <app>~<env>-<id>

    Examples::

        PROJECTPLACE~pp-333334444
        E1_PRM~p-31mgpdqajn|integ18_e1_lk
        LEANKIT~d03-10127547577
    """

    OKRS_SYSTEM_CODE = "okrs"
    APP_SYSTEM_CODES = {"leankit": "lk"}

    def __init__(self, tenant_id_str):
        """
        Initialize the tenant parser.

        :param str tenant_id_str: the tenant_id_str from the database column
        """
        self.tenant_id_str = tenant_id_str or ""

    @property
    def tenant_code(self):
        """Return the `tenant_id_str`. This is an alias."""
        return self.tenant_id_str

    @property
    def tenant_app(self):
        """Return the tenant app portion of the tenant code."""
        return self.tenant_code.split("~")[0]

    @property
    def app_system_code(self):
        """Return the system code for the application."""
        return self.APP_SYSTEM_CODES[self.tenant_app.lower()]

    @property
    def tenant_env(self):
        """Return the environment portion of the tenant code."""
        return self._tenant_code_end.split("-")[0]

    @property
    def tenant_id(self):
        """Return the identifier portion of the tenant code."""
        return self._tenant_code_end.split("-")[-1]

    @property
    def okrs_tenant_id(self):
        """Return the tenant id for OKRs."""
        return f"{self.OKRS_SYSTEM_CODE}-{self.tenant_env}-{self.tenant_id}"

    @property
    def _tenant_code_end(self):
        """Return everything in the tenant code after the tenant app."""
        return self.tenant_code.split("~")[-1]
