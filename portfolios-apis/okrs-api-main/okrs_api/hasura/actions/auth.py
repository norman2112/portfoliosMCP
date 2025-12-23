"""All authentication-related functions."""

import json
import os
import re
import jwt
import requests

from okrs_api.utils import lower_keys, normalise
from okrs_api.validators.errors import ValidationError


class PayloadParserBase:
    """The base parser for the JWT payload."""

    HASURA_CLAIMS_KEY = "https://hasura.io/jwt/claims"
    APP_DOMAIN_KEY = "app_domain"

    def __init__(self, payload_data):
        """Initialize with the payload data."""
        self.payload_data = payload_data
        self.memo = {}

    def hasura_claims(self):
        """Return the hasura claims portion of the JWT."""
        raise NotImplementedError

    @property
    def hasura_org_id(self):
        """Get the hasura_org_id from the JWT."""
        org_id = self.hasura_claims().get("x-hasura-platforma-app-tenant-id", None)

        if org_id is None:
            org_id = self.hasura_claims().get("x-hasura-org-id")

        return org_id

    @property
    def hasura_org_id_original(self):
        """Get the x-hasura-org-id from JWT."""
        return self.hasura_claims().get("x-hasura-org-id", "")

    @property
    def hasura_app_tenant_id_original(self):
        """Get the x-hasura-org-id from JWT."""
        return self.hasura_claims().get("x-hasura-platforma-app-tenant-id", None)

    @property
    def hasura_tenant_group_id(self):
        """Get the tenant_group_id from the JWT."""
        tenant_group_id = self.hasura_claims().get("x-hasura-tenant-group-id", "")
        if not tenant_group_id:
            tenant_group_id = self.hasura_claims().get("x-hasura-org-id", "")

        return tenant_group_id

    @property
    def hasura_tenant_group_id_original(self):
        """Get the original value of tenant_group_id from JWT, not the fallback value."""

        return self.hasura_claims().get("x-hasura-tenant-group-id", "")

    @property
    def hasura_app_name(self):
        """Get the hasura_app_name from the JWT."""
        return self.hasura_claims().get("x-hasura-app-name")

    @property
    def planview_user_id(self):
        """Get the planview user if from JWT."""
        pv_user_id = self.hasura_claims().get("x-hasura-planview-user-id", "")

        if not pv_user_id:
            pv_user_id = self.hasura_claims().get("x-hasura-user-id", "")

        return pv_user_id

    @property
    def user_id(self):
        """Return the user id."""
        return self.hasura_claims().get("x-hasura-platforma-app-user-id")


class PlanviewTokenServicePayloadParser(PayloadParserBase):
    """Parser for the Planview Token Service Payload."""

    def hasura_claims(self):
        """
        Return the hasura claims portion of the JWT.

        The Hasura claims section for the Planview Token Service is a JSON
        string, and must first be parsed, before it can be accessed.
        See more here:
        https://github.com/pv-platforma/infra/wiki/Planview-Token-Service#jwt-token

        Memoize the result.
        """
        if not self.memo.get("hasura_claims"):
            claims = self.payload_data.get(self.HASURA_CLAIMS_KEY)
            claims_dict = json.loads(claims)
            self.memo["hasura_claims"] = lower_keys(claims_dict)

        return self.memo["hasura_claims"]

    @property
    def planview_admin_url(self):
        """Return the planview admin url if present."""
        return self.payload_data.get("planview_admin_url")

    @property
    def app_domain(self):
        """Return the app domain in the token."""
        app_domain = self.payload_data.get(self.APP_DOMAIN_KEY, "")
        if not app_domain:
            print(
                "WARNING: PTS token does not contain an app domain {}".format(
                    self.payload_data
                )
            )
        return app_domain


class JWTParser:
    """Base parser class to get fields from the authentication JWT."""

    def __init__(self, request_headers):
        """
        Initialize the arguments to parse the user id.

        :param dict request_headers: the request headers
        """
        self.request_headers = request_headers
        self.errors = []
        self.memo = {}

    @property
    def hasura_jwt(self):
        """
        Return the incoming JWT, sent in the authorization header.

        JWTs are provided to Hasura. If, "include headers" is checked for a
        custom action, then JWT that was provided to Hasura is also provided
        to this API.
        """
        auth_value = self.request_headers.get("Authorization")
        if not auth_value:
            return None

        return re.sub(r"^Bearer\s+", "", auth_value, re.IGNORECASE)

    @property
    def payload(self):
        """
        Return the payload in the form of a payload parser.

        Memoize the result.
        """
        if not self.memo.get("payload"):
            payload_data = self._get_payload_data()
            payload_data = lower_keys(payload_data)
            self.memo["payload"] = PlanviewTokenServicePayloadParser(payload_data)

        return self.memo["payload"]

    @property
    def user_id(self):
        """Get the app user_id from the payload."""
        return self.payload.user_id

    @property
    def planview_user_id(self):
        """Get the planview user id from payload."""
        return self.payload.planview_user_id

    @property
    def hasura_org_id_original(self):
        """Return the org id from the payload."""
        return self.payload.hasura_org_id_original

    @property
    def hasura_app_tenant_id_original(self):
        """Return the tenant group id from the payload."""
        return self.payload.hasura_app_tenant_id_original

    @property
    def hasura_org_id(self):
        """Return the org id from the payload."""
        return self.payload.hasura_org_id

    @property
    def hasura_tenant_group_id(self):
        """Return the tenant group id from the payload."""
        return self.payload.hasura_tenant_group_id

    @property
    def hasura_tenant_group_id_original(self):
        """Return original, non fallback value from payload."""
        return self.payload.hasura_tenant_group_id_original

    @property
    def planview_admin_url(self):
        """Return the planview admin url from the payload."""
        return self.payload.planview_admin_url

    @property
    def hasura_app_name(self):
        """Return the app name from the payload."""
        return self.payload.hasura_app_name

    @property
    def app_domain(self):
        """Return the app domain from the payload."""
        return normalise(self.payload.app_domain)

    def validate(self):
        """Validate the JWT payload data."""
        validation_functions = [
            self._validate_jwt,
            self._validate_hasura_org_id,
            self._validate_user_id,
        ]

        for vfunc in validation_functions:
            if not vfunc():
                return False

        return True

    def _get_payload_data(self):
        """
        Return the JWT payload data.

        Hasura has already verified the JWT. Since this api is not
        publicly accessible, we can trust the JWT from Hasura.
        """

        try:
            return jwt.decode(
                self.hasura_jwt,
                options={
                    "verify_signature": False,
                    "verify_aud": False,
                    "verify_exp": self._should_validate_expiration(),
                },
            )
        except jwt.exceptions.DecodeError:
            self.errors.append(
                ValidationError(code="jwt_error", message="Invalid token.")
            )
            return {}

    def _should_validate_expiration(self):
        """
        Validate expiration if in production.

        This allows local development or the CI to not have to worry about a PTS
        token expiring.
        """
        return os.environ.get("CONNEXION_ENVIRONMENT") == "production"

    def _validate_jwt(self):
        """
        Validate if payload data was returned.

        An error is added if no payload data.
        """
        return bool(self._get_payload_data())

    def _validate_user_id(self):
        if self.user_id or self.planview_user_id:
            return True

        self.errors.append(
            ValidationError(
                code="user_id_authorization", message="JWT is missing a User ID."
            )
        )
        return False

    def _validate_hasura_org_id(self):
        if self.hasura_org_id or self.hasura_tenant_group_id:
            return True

        self.errors.append(
            ValidationError(
                code="org_id_authorization", message="JWT is missing an Org ID."
            )
        )
        return False


class OKRTokenGenerator:
    """PTS token generator for OKRs."""

    def __init__(self, input_prepper, product_type):
        """Initialise with an input prepper object."""
        self.input_prepper = input_prepper
        self.domains = self.input_prepper.applications["domains"]
        self.product_type = product_type

    def _get_roles(self):
        """Get list of roles from the original JWT token."""
        return self.input_prepper.jwt_parser.payload.hasura_claims().get(
            "x-hasura-allowed-roles"
        )

    def _get_role(self):
        """Get the primary role."""
        return self.input_prepper.jwt_parser.payload.hasura_claims().get(
            "x-hasura-default-role"
        )

    def _get_planview_group_id(self):
        """Get the group tenant id."""
        return self.input_prepper.tenant_group_id

    def _get_planview_user_id(self):
        """Get pvadmin user id."""
        return self.input_prepper.planview_user_id

    def _get_env_selector(self):
        """Get the env selector."""
        return self.input_prepper.applications["env_selectors"].get(self.product_type)

    def _get_app_tenant_id(self):
        """Get the app specific tenant id."""
        env_selector = self._get_env_selector()
        parts = env_selector.split("~")
        if len(parts) > 1:
            return parts[1]

        return env_selector

    def _get_app_user_id(self):
        """Get the app specific user id."""
        return self.input_prepper.applications["app_users"].get(self.product_type)

    def generate_token(self):
        """
        Generate token based on input and environment parameters.

        ENV variables needed:

        - `PLANVIEW_TOKEN_SERVICE_CLIENT_ID`: the client id for PTS
        - `PLANVIEW_TOKEN_SERVICE_CLIENT_SECRET`: the client secret for PTS
        - `PLANVIEW_TOKEN_SERVICE_REGION`: the region for the service. Default ('us-west-2')
        """

        region = os.environ.get("PLANVIEW_TOKEN_SERVICE_REGION") or "us-west-2"
        client_id_env_var = "PLANVIEW_TOKEN_SERVICE_CLIENT_ID"
        client_secret_env_var = "PLANVIEW_TOKEN_SERVICE_CLIENT_SECRET"

        if client_id_env_var not in os.environ:
            print(f"{client_id_env_var} environment variable required")
            return None

        if client_secret_env_var not in os.environ:
            print(f"{client_secret_env_var} environment variable required")
            return None

        app_tenant_id = self._get_app_tenant_id()
        app_user_id = self._get_app_user_id()

        data = {
            "client_id": os.environ[client_id_env_var],
            "client_secret": os.environ[client_secret_env_var],
            "application_name": str(self.product_type),
            "application_domain": str(
                "https://" + self.domains.get(self.product_type, "")
            ),
            "application_roles": self._get_roles(),
            "application_account_id": app_tenant_id,
            "application_user_id": app_user_id,
            "application_context_id": None,
            "role": self._get_role(),
            "account_id": app_tenant_id,
            "user_id": app_user_id,
            "planview_tenant_group_id": self._get_planview_group_id(),
            "planview_user_id": self._get_planview_user_id(),
            "planview_env_selector": self._get_env_selector(),
            "sections": "app,platforma,planview",
        }

        response = requests.post(
            f"https://auth-{region}.pv-platforma.xyz/oauth2/token", data=data
        )

        jwt_token = response.json()["id_token"]
        return jwt_token
