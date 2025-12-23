"""Define the root conftest."""
import base64
import pathlib
from unittest.mock import patch

from sqlalchemy import create_engine
from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from open_alchemy import models
import pytest
from pytest_factoryboy import register
import sqlalchemy

from okrs_api import connexion_utils
from okrs_api import settings
from okrs_api.hasura.events.event_parser import EventParser

from tests import models_loader
from tests.factories.support import factory_initializer

ROOT_DIR = pathlib.Path(__file__).parent.parent

# The following creates fixtures that can be used to directly access
# FactoryBot factories.
# Refer here for more information:
# https://pytest-factoryboy.readthedocs.io/en/latest/#factory-fixture
for factory_cls in factory_initializer.import_factories():
    if not factory_cls._meta.abstract:
        register(factory_cls)


@pytest.fixture()
def connexion_app():
    """Create a connexion app."""
    return connexion_utils.create_connexion_app("local")


@pytest.fixture()
def app_settings(connexion_app):
    """Return the settings for the app."""
    return connexion_app.app["settings"]


# pylint: disable=redefined-outer-name
#   We are using a fixture previously defined.
@pytest.fixture
async def connexion_client(aiohttp_client, connexion_app):
    """Create a connexion client."""
    return await aiohttp_client(connexion_app.app)


@pytest.fixture(scope="session")
def offline_connexion_app():
    """Create a connexion app."""
    with patch.dict("os.environ", {"CONNEXION_ENVIRONMENT": "local"}):
        with patch.dict(
            "os.environ", {"DATABASE_URL": "postgresql://localhost/postgres"}
        ):
            app = connexion_utils.create_connexion_app()
            return app


# pylint: disable=redefined-outer-name
#   We are using a fixture previously defined.
@pytest.fixture
async def offline_connexion_client(aiohttp_client, offline_connexion_app):
    """Create a connexion client."""
    return await aiohttp_client(offline_connexion_app.app)


@pytest.fixture(scope="session", autouse=True)
def init_models():
    """Initialize the models."""
    models_loader.initialize_models()


@pytest.fixture(scope="module")
def vcr_config():
    """
    Set the VCR plugin config.

    Replace any Authorization request headers with "REDACTED" in cassettes.
    """
    # TODO: PLease put the host back into the matchers.
    # In order to make this work again with the test server, we had to take out
    # the `host` matcher. But this isn't ideal.
    # https://vcrpy.readthedocs.io/en/latest/configuration.html
    # - eric 2021-01-14
    # "match_on": ["method", "scheme", "host", "path", "query"],
    return {
        "match_on": ["method", "scheme", "path", "query"],
        "filter_headers": [("authorization", "REDACTED")],
        "filter_post_data_parameters": [
            ("client_id", "REDACTED"),
            ("client_secret", "REDACTED"),
        ],
    }


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    """Set the cassette dir for the test cassette."""
    return str(ROOT_DIR / "tests/cassettes" / request.module.__name__)


@pytest.fixture(scope="session")
def db_settings():
    """
    Return the database settings from the application settings.

    This is set to 'local' as this is the only environment we wish to test in.
    """
    return settings.get("local").database


@pytest.fixture(scope="module")
def db_connection(db_settings):
    """Create a database connection to the engine specified in settings."""
    db_settings_dict = db_settings.engine.dict()
    db_url = db_settings_dict.pop("name_or_url")
    engine = create_engine(db_url, **db_settings_dict)
    connection = engine.connect()
    yield connection
    connection.close()


@pytest.fixture(scope="function")
def add_session_to_factories():
    """
    Initialize all factories with the db session of your choice.

    Returns the function that you may then pass in the appropriate db_session
    to. This db_session may be a real SqlAlchemy session or a mock one.
    """
    return factory_initializer.add_db_session_to_factories


@pytest.fixture(scope="function")
def db_session(db_settings, db_connection, add_session_to_factories):
    """
    Create a database session that operates within a transaction.

    This session uses a transaction to undo any changes done.

    This will also update all FactoryBot factories with the `db_session` that is
    created here. This will allow the factories to automatically create
    records in the database upon initialization.
    """
    transaction = db_connection.begin()
    db_session = sqlalchemy.orm.scoped_session(
        sqlalchemy.orm.sessionmaker(bind=db_connection)
    )
    add_session_to_factories(db_session)
    yield db_session
    db_session.close()
    transaction.rollback()


@pytest.fixture
def dummy_pts_token():
    """
    Return a dummy Planview Token Service JWT.

    The JWT fits the shape of the Planview Token Service but is signed with
    'secret' and is missing the 'aud' key.

    Payload::

        {
          "sub": "3997fc41-d0ec-4eaf-84d2-7bc3e21f5715",
          "https://hasura.io/jwt/claims": "{\"X-HASURA-DEFAULT-ROLE\": \"user\", \"X-HASURA-APP-NAME\": \"leankit\", \"X-HASURA-ALLOWED-ROLES\": [\"user\"], \"X-HASURA-USER-ID\": \"10145734719\", \"X-HASURA-ORG-ID\": \"LEANKIT~d12-123\", \"X-HASURA-PLATFORMA-APP-TENANT-ID\": \"LEANKIT~d12-123\", \"X-HASURA-PLATFORMA-APP-USER-ID\": \"10145734719\"}",
          "iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_EgR4jyqiX",
          "app_domain": "d09.leankit.io",
          "cognito:username": "platforma-user",
          "app_context_id": "10136408886",
          "platforma_user_id": "10145734719",
          "app_name": "leankit",
          "event_id": "6422cb89-655c-485c-bbb8-10a5454cb84f",
          "platforma_role": "user",
          "app_user_id": "10145734719",
          "token_use": "id",
          "platforma_account_id": "LEANKIT~d12-123",
          "auth_time": 1631100000,
          "app_account_id": "10113280894",
          "exp": 16354602049,
          "app_roles": "user",
          "iat": 1635456604
        }

    https://github.com/pv-platforma/infra/wiki/Planview-Token-Service#jwt-token
    """
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjoie1wiWC1IQVNVUkEtREVGQVVMVC1ST0xFXCI6IFwidXNlclwiLCBcIlgtSEFTVVJBLUFQUC1OQU1FXCI6IFwibGVhbmtpdFwiLCBcIlgtSEFTVVJBLUFMTE9XRUQtUk9MRVNcIjogW1widXNlclwiXSwgXCJYLUhBU1VSQS1VU0VSLUlEXCI6IFwiMTAxNDU3MzQ3MTlcIiwgXCJYLUhBU1VSQS1PUkctSURcIjogXCJMRUFOS0lUfmQxMi0xMjNcIiwgXCJYLUhBU1VSQS1QTEFURk9STUEtQVBQLVRFTkFOVC1JRFwiOiBcIkxFQU5LSVR-ZDEyLTEyM1wiLCBcIlgtSEFTVVJBLVBMQVRGT1JNQS1BUFAtVVNFUi1JRFwiOiBcIjEwMTQ1NzM0NzE5XCJ9IiwiaXNzIjoiaHR0cHM6Ly9jb2duaXRvLWlkcC51cy13ZXN0LTIuYW1hem9uYXdzLmNvbS91cy13ZXN0LTJfRWdSNGp5cWlYIiwiYXBwX2RvbWFpbiI6ImQwOS5sZWFua2l0LmlvIiwiY29nbml0bzp1c2VybmFtZSI6InBsYXRmb3JtYS11c2VyIiwiYXBwX2NvbnRleHRfaWQiOiIxMDEzNjQwODg4NiIsInBsYXRmb3JtYV91c2VyX2lkIjoiMTAxNDU3MzQ3MTkiLCJhcHBfbmFtZSI6ImxlYW5raXQiLCJldmVudF9pZCI6IjY0MjJjYjg5LTY1NWMtNDg1Yy1iYmI4LTEwYTU0NTRjYjg0ZiIsInBsYXRmb3JtYV9yb2xlIjoidXNlciIsImFwcF91c2VyX2lkIjoiMTAxNDU3MzQ3MTkiLCJ0b2tlbl91c2UiOiJpZCIsInBsYXRmb3JtYV9hY2NvdW50X2lkIjoiTEVBTktJVH5kMTItMTIzIiwiYXV0aF90aW1lIjoxNjMxMTAwMDAwLCJhcHBfYWNjb3VudF9pZCI6IjEwMTEzMjgwODk0IiwiZXhwIjoxNjM1NDYwMjA0OSwiYXBwX3JvbGVzIjoidXNlciIsImlhdCI6MTYzNTQ1NjYwNH0.dqVp8_WZ8PnzUFF2pVQZdXNQfZHP94pVzTrMA3WjVYc"


@pytest.fixture
def dummy_pts_pvadmin_token():
    """
    Return a dummy Planview Token Service JWT for a customer with PVAdmin.

    The JWT fits the shape of the Planview Token Service but is signed with
    'secret' and is missing the 'aud' key.

    Payload::

        {
          "sub": "3997fc41-d0ec-4eaf-84d2-7bc3e21f5715",
          "https://hasura.io/jwt/claims": "{\"X-HASURA-DEFAULT-ROLE\": \"user\", \"X-HASURA-APP-NAME\": \"leankit\", \"X-HASURA-ALLOWED-ROLES\": [\"user\"], \"X-HASURA-USER-ID\": \"dfdsfs213213213321\", \"X-HASURA-ORG-ID\": \"1231231234\", \"X-HASURA-PLATFORMA-APP-TENANT-ID\": \"LEANKIT~d12-123\", \"X-HASURA-PLATFORMA-APP-USER-ID\": \"10145734719\"}",
          "iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_EgR4jyqiX",
          "app_domain": "d09.leankit.io",
          "cognito:username": "platforma-user",
          "app_context_id": "10136408886",
          "platforma_user_id": "10145734719",
          "app_name": "leankit",
          "event_id": "6422cb89-655c-485c-bbb8-10a5454cb84f",
          "platforma_role": "user",
          "app_user_id": "10145734719",
          "token_use": "id",
          "platforma_account_id": "LEANKIT~d12-123",
          "auth_time": 1631100000,
          "app_account_id": "10113280894",
          "exp": 16354602049,
          "app_roles": "user",
          "iat": 1635456604
        }

    https://github.com/pv-platforma/infra/wiki/Planview-Token-Service#jwt-token
    """
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjoie1wiWC1IQVNVUkEtREVGQVVMVC1ST0xFXCI6IFwidXNlclwiLCBcIlgtSEFTVVJBLUFQUC1OQU1FXCI6IFwibGVhbmtpdFwiLCBcIlgtSEFTVVJBLUFMTE9XRUQtUk9MRVNcIjogW1widXNlclwiXSwgXCJYLUhBU1VSQS1VU0VSLUlEXCI6IFwiZGZkc2ZzMjEzMjEzMjEzMzIxXCIsIFwiWC1IQVNVUkEtT1JHLUlEXCI6IFwiMTIzMTIzMTIzNFwiLCBcIlgtSEFTVVJBLVBMQVRGT1JNQS1BUFAtVEVOQU5ULUlEXCI6IFwiTEVBTktJVH5kMTItMTIzXCIsIFwiWC1IQVNVUkEtUExBVEZPUk1BLUFQUC1VU0VSLUlEXCI6IFwiMTAxNDU3MzQ3MTlcIn0iLCJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLnVzLXdlc3QtMi5hbWF6b25hd3MuY29tL3VzLXdlc3QtMl9FZ1I0anlxaVgiLCJhcHBfZG9tYWluIjoiZDA5LmxlYW5raXQuaW8iLCJjb2duaXRvOnVzZXJuYW1lIjoicGxhdGZvcm1hLXVzZXIiLCJhcHBfY29udGV4dF9pZCI6IjEwMTM2NDA4ODg2IiwicGxhdGZvcm1hX3VzZXJfaWQiOiIxMDE0NTczNDcxOSIsImFwcF9uYW1lIjoibGVhbmtpdCIsImV2ZW50X2lkIjoiNjQyMmNiODktNjU1Yy00ODVjLWJiYjgtMTBhNTQ1NGNiODRmIiwicGxhdGZvcm1hX3JvbGUiOiJ1c2VyIiwiYXBwX3VzZXJfaWQiOiIxMDE0NTczNDcxOSIsInRva2VuX3VzZSI6ImlkIiwicGxhdGZvcm1hX2FjY291bnRfaWQiOiJMRUFOS0lUfmQxMi0xMjMiLCJhdXRoX3RpbWUiOjE2MzExMDAwMDAsImFwcF9hY2NvdW50X2lkIjoiMTAxMTMyODA4OTQiLCJleHAiOjE2MzU0NjAyMDQ5LCJhcHBfcm9sZXMiOiJ1c2VyIiwiaWF0IjoxNjM1NDU2NjA0fQ.mIevCCsqERh-HVAGYPQwjm6GP7RbOXoGzyvtNyX49Sg"


@pytest.fixture
def dummy_pts_pvadmin_settings_token():
    """
    Return a dummy Planview Token Service JWT for a customer with PVAdmin.

    The JWT fits the shape of the Planview Token Service but is signed with
    'secret' and is missing the 'aud' key.

    Payload::

        {
          "sub": "3997fc41-d0ec-4eaf-84d2-7bc3e21f5715",
          "https://hasura.io/jwt/claims": "{\"X-HASURA-DEFAULT-ROLE\": \"user\", \"X-HASURA-APP-NAME\": \"\", \"X-HASURA-ALLOWED-ROLES\": [\"user\"], \"X-HASURA-USER-ID\": \"dfdsfs213213213321\", \"X-HASURA-ORG-ID\": \"1231231234\", \"X-HASURA-PLATFORMA-APP-TENANT-ID\": \"\", \"X-HASURA-PLATFORMA-APP-USER-ID\": \"\"}",
          "iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_EgR4jyqiX",
          "app_domain": "d09.leankit.io",
          "cognito:username": "platforma-user",
          "app_context_id": "10136408886",
          "platforma_user_id": "10145734719",
          "app_name": "leankit",
          "event_id": "6422cb89-655c-485c-bbb8-10a5454cb84f",
          "platforma_role": "user",
          "app_user_id": "10145734719",
          "token_use": "id",
          "platforma_account_id": "LEANKIT~d12-123",
          "auth_time": 1631100000,
          "app_account_id": "10113280894",
          "exp": 16354602049,
          "app_roles": "user",
          "iat": 1635456604
        }

    https://github.com/pv-platforma/infra/wiki/Planview-Token-Service#jwt-token
    """
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjoie1wiWC1IQVNVUkEtREVGQVVMVC1ST0xFXCI6IFwidXNlclwiLCBcIlgtSEFTVVJBLUFQUC1OQU1FXCI6IFwiXCIsIFwiWC1IQVNVUkEtQUxMT1dFRC1ST0xFU1wiOiBbXCJ1c2VyXCJdLCBcIlgtSEFTVVJBLVVTRVItSURcIjogXCJkZmRzZnMyMTMyMTMyMTMzMjFcIiwgXCJYLUhBU1VSQS1PUkctSURcIjogXCIxMjMxMjMxMjM0XCIsIFwiWC1IQVNVUkEtUExBVEZPUk1BLUFQUC1URU5BTlQtSURcIjogXCJcIiwgXCJYLUhBU1VSQS1QTEFURk9STUEtQVBQLVVTRVItSURcIjogXCJcIn0iLCJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLnVzLXdlc3QtMi5hbWF6b25hd3MuY29tL3VzLXdlc3QtMl9FZ1I0anlxaVgiLCJhcHBfZG9tYWluIjoiZDA5LmxlYW5raXQuaW8iLCJjb2duaXRvOnVzZXJuYW1lIjoicGxhdGZvcm1hLXVzZXIiLCJhcHBfY29udGV4dF9pZCI6IjEwMTM2NDA4ODg2IiwicGxhdGZvcm1hX3VzZXJfaWQiOiIxMDE0NTczNDcxOSIsImFwcF9uYW1lIjoibGVhbmtpdCIsImV2ZW50X2lkIjoiNjQyMmNiODktNjU1Yy00ODVjLWJiYjgtMTBhNTQ1NGNiODRmIiwicGxhdGZvcm1hX3JvbGUiOiJ1c2VyIiwiYXBwX3VzZXJfaWQiOiIxMDE0NTczNDcxOSIsInRva2VuX3VzZSI6ImlkIiwicGxhdGZvcm1hX2FjY291bnRfaWQiOiJMRUFOS0lUfmQxMi0xMjMiLCJhdXRoX3RpbWUiOjE2MzExMDAwMDAsImFwcF9hY2NvdW50X2lkIjoiMTAxMTMyODA4OTQiLCJleHAiOjE2MzU0NjAyMDQ5LCJhcHBfcm9sZXMiOiJ1c2VyIiwiaWF0IjoxNjM1NDU2NjA0fQ.RDx7pbNCxnR0-ENoeJvpj3UP7PWvoWx4zrUDqiqJ4r8"


@pytest.fixture
def dummy_pts_token_with_pvadmin_url():
    """
    Return a dummy Planview Token Service JWT.

    The JWT fits the shape of the Planview Token Service but is signed with
    'secret' and is missing the 'aud' key.

    Payload::

        {
          "sub": "3997fc41-d0ec-4eaf-84d2-7bc3e21f5715",
          "https://hasura.io/jwt/claims": "{\"X-HASURA-DEFAULT-ROLE\": \"user\", \"X-HASURA-ALLOWED-ROLES\": [\"user\"], \"X-HASURA-USER-ID\": \"10145734719\", \"X-HASURA-ORG-ID\": \"LEANKIT~d12-123\"}",
          "iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_EgR4jyqiX",
          "app_domain": "d09.leankit.io",
          "cognito:username": "platforma-user",
          "app_context_id": "10136408886",
          "platforma_user_id": "10145734719",
          "app_name": "leankit",
          "event_id": "6422cb89-655c-485c-bbb8-10a5454cb84f",
          "platforma_role": "user",
          "app_user_id": "10145734719",
          "token_use": "id",
          "platforma_account_id": "LEANKIT~d12-123",
          "auth_time": 1631100000,
          "app_account_id": "10113280894",
          "exp": 16354602049,
          "app_roles": "user",
          "iat": 1635456604
        }

    https://github.com/pv-platforma/infra/wiki/Planview-Token-Service#jwt-token
    """
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjoie1wiWC1IQVNVUkEtREVGQVVMVC1ST0xFXCI6IFwidXNlclwiLCBcIlgtSEFTVVJBLUFMTE9XRUQtUk9MRVNcIjogW1widXNlclwiXSwgXCJYLUhBU1VSQS1VU0VSLUlEXCI6IFwiMTAxNDU3MzQ3MTlcIiwgXCJYLUhBU1VSQS1PUkctSURcIjogXCJMRUFOS0lUfmQxMi0xMjNcIn0iLCJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLnVzLXdlc3QtMi5hbWF6b25hd3MuY29tL3VzLXdlc3QtMl9FZ1I0anlxaVgiLCJhcHBfZG9tYWluIjoiZDA5LmxlYW5raXQuaW8iLCJjb2duaXRvOnVzZXJuYW1lIjoicGxhdGZvcm1hLXVzZXIiLCJhcHBfY29udGV4dF9pZCI6IjEwMTM2NDA4ODg2IiwicGxhdGZvcm1hX3VzZXJfaWQiOiIxMDE0NTczNDcxOSIsImFwcF9uYW1lIjoibGVhbmtpdCIsImV2ZW50X2lkIjoiNjQyMmNiODktNjU1Yy00ODVjLWJiYjgtMTBhNTQ1NGNiODRmIiwicGxhdGZvcm1hX3JvbGUiOiJ1c2VyIiwiYXBwX3VzZXJfaWQiOiIxMDE0NTczNDcxOSIsInRva2VuX3VzZSI6ImlkIiwicGxhdGZvcm1hX2FjY291bnRfaWQiOiJMRUFOS0lUfmQxMi0xMjMiLCJhdXRoX3RpbWUiOjE2MzExMDAwMDAsImFwcF9hY2NvdW50X2lkIjoiMTAxMTMyODA4OTQiLCJleHAiOjE2MzU0NjAyMDQ5LCJhcHBfcm9sZXMiOiJ1c2VyIiwicGxhbnZpZXdfYWRtaW5fdXJsIjoicHZpZC5zb21lc2l0ZS5wbGFudmlldy5jb20iLCJpYXQiOjE2MzU0NTY2MDR9.y8A-kxAqQoJeWTeavHyHDO3X_V6Y5-5BTIbGw_PNATA"


@pytest.fixture
def dummy_pts_token_with_pvadmin_url_https():
    """
    Return a dummy Planview Token Service JWT.

    The JWT fits the shape of the Planview Token Service but is signed with
    'secret' and is missing the 'aud' key.

    Payload::

        {
          "sub": "3997fc41-d0ec-4eaf-84d2-7bc3e21f5715",
          "https://hasura.io/jwt/claims": "{\"X-HASURA-DEFAULT-ROLE\": \"user\", \"X-HASURA-ALLOWED-ROLES\": [\"user\"], \"X-HASURA-USER-ID\": \"10145734719\", \"X-HASURA-ORG-ID\": \"LEANKIT~d12-123\"}",
          "iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_EgR4jyqiX",
          "app_domain": "d09.leankit.io",
          "cognito:username": "platforma-user",
          "app_context_id": "10136408886",
          "platforma_user_id": "10145734719",
          "app_name": "leankit",
          "event_id": "6422cb89-655c-485c-bbb8-10a5454cb84f",
          "platforma_role": "user",
          "app_user_id": "10145734719",
          "token_use": "id",
          "platforma_account_id": "LEANKIT~d12-123",
          "auth_time": 1631100000,
          "app_account_id": "10113280894",
          "exp": 16354602049,
          "app_roles": "user",
          "planview_admin_url": "https://pvid.somesite.planview.com",
          "iat": 1635456604
        }

    https://github.com/pv-platforma/infra/wiki/Planview-Token-Service#jwt-token
    """
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJodHRwczovL2hhc3VyYS5pby9qd3QvY2xhaW1zIjoie1wiWC1IQVNVUkEtREVGQVVMVC1ST0xFXCI6IFwidXNlclwiLCBcIlgtSEFTVVJBLUFMTE9XRUQtUk9MRVNcIjogW1widXNlclwiXSwgXCJYLUhBU1VSQS1VU0VSLUlEXCI6IFwiMTAxNDU3MzQ3MTlcIiwgXCJYLUhBU1VSQS1PUkctSURcIjogXCJMRUFOS0lUfmQxMi0xMjNcIn0iLCJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLnVzLXdlc3QtMi5hbWF6b25hd3MuY29tL3VzLXdlc3QtMl9FZ1I0anlxaVgiLCJhcHBfZG9tYWluIjoiZDA5LmxlYW5raXQuaW8iLCJjb2duaXRvOnVzZXJuYW1lIjoicGxhdGZvcm1hLXVzZXIiLCJhcHBfY29udGV4dF9pZCI6IjEwMTM2NDA4ODg2IiwicGxhdGZvcm1hX3VzZXJfaWQiOiIxMDE0NTczNDcxOSIsImFwcF9uYW1lIjoibGVhbmtpdCIsImV2ZW50X2lkIjoiNjQyMmNiODktNjU1Yy00ODVjLWJiYjgtMTBhNTQ1NGNiODRmIiwicGxhdGZvcm1hX3JvbGUiOiJ1c2VyIiwiYXBwX3VzZXJfaWQiOiIxMDE0NTczNDcxOSIsInRva2VuX3VzZSI6ImlkIiwicGxhdGZvcm1hX2FjY291bnRfaWQiOiJMRUFOS0lUfmQxMi0xMjMiLCJhdXRoX3RpbWUiOjE2MzExMDAwMDAsImFwcF9hY2NvdW50X2lkIjoiMTAxMTMyODA4OTQiLCJleHAiOjE2MzU0NjAyMDQ5LCJhcHBfcm9sZXMiOiJ1c2VyIiwicGxhbnZpZXdfYWRtaW5fdXJsIjoiaHR0cHM6Ly9wdmlkLnNvbWVzaXRlLnBsYW52aWV3LmNvbSIsImlhdCI6MTYzNTQ1NjYwNH0.GNDjDDlUzGRpjRv39WKVJzRfOHjwcX9JJ4t0OqepNSk"


@pytest.fixture
def dummy_pts_token_with_id_token():
    """Return a valid ID token (most likely expired)"""
    return "eyJraWQiOiJYc3YwZEVyU2habm9LaVF5SGp6OWdrdE9LSnZ1N0kxUkJOb0pSOEtHcmZrPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJiN2UzNjU2YS1lNjIyLTQwZDYtOGNkYy00NWI1YThmODQ0NWUiLCJwbGFudmlld19kZXBsb3ltZW50X2lkIjoiIiwicGxhbnZpZXdfY3VzdG9tZXJfaWQiOiJYMTAwIiwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLXdlc3QtMi5hbWF6b25hd3MuY29tXC91cy13ZXN0LTJfbHRVdHlkVXdmIiwiYXBwX2RvbWFpbiI6ImQwMy5sZWFua2l0LmlvIiwiYXBwX2NvbnRleHRfaWQiOiIiLCJwbGF0Zm9ybWFfdXNlcl9pZCI6ImQwMy0xMDEyNzgwNjQyNl8xMDEyNzgwNjQzMyIsImFwcF9jb250ZXh0IjoiIiwicGxhbnZpZXdfdGVuYW50X2dyb3VwX2lkIjoiNzI3YTFjZDEtYzhiOC00NDVmLWFjNTMtYmNiM2Q5OWIxMDkxOnAiLCJhdXRoX3RpbWUiOjE2NTMzOTE1MzUsImFwcF9hY2NvdW50X2lkIjoiZDAzLTEwMTI3ODA2NDI2IiwiZXhwIjoxNjUzMzk1MTM1LCJhcHBfcm9sZXMiOiJhZG1pbiIsImlhdCI6MTY1MzM5MTUzNSwianRpIjoiYjk3NWVjMzctMTRhYS00NzE1LWJlODktZjc4Mjk3YTgxZDk3IiwicGxhbnZpZXdfdXNlcl9pZCI6IlUxMDQiLCJodHRwczpcL1wvaGFzdXJhLmlvXC9qd3RcL2NsYWltcyI6IntcIlgtSEFTVVJBLURFRkFVTFQtUk9MRVwiOiBcImFkbWluXCIsIFwiWC1IQVNVUkEtQUxMT1dFRC1ST0xFU1wiOiBbXCJhZG1pblwiXSwgXCJYLUhBU1VSQS1VU0VSLUlEXCI6IFwiVTEwNFwiLCBcIlgtSEFTVVJBLU9SRy1JRFwiOiBcIjcyN2ExY2QxLWM4YjgtNDQ1Zi1hYzUzLWJjYjNkOTliMTA5MTpwXCIsIFwiWC1IQVNVUkEtVEVOQU5ULUdST1VQLUlEXCI6IFwiNzI3YTFjZDEtYzhiOC00NDVmLWFjNTMtYmNiM2Q5OWIxMDkxOnBcIiwgXCJYLUhBU1VSQS1URU5BTlQtSURcIjogXCJkMDMtMTAxMjc4MDY0MjZcIiwgXCJYLUhBU1VSQS1QTEFOVklFVy1VU0VSLUlEXCI6IFwiVTEwNFwiLCBcIlgtSEFTVVJBLUFQUC1VU0VSLUlEXCI6IFwiZDAzLTEwMTI3ODA2NDI2XzEwMTI3ODA2NDMzXCIsIFwiWC1IQVNVUkEtQVBQLU5BTUVcIjogXCJsZWFua2l0XCJ9IiwiY29nbml0bzp1c2VybmFtZSI6InBsYXRmb3JtYS11c2VyIiwib3JpZ2luX2p0aSI6IjE4MTQwNGQxLTEzYTQtNDk5Yy05MGU0LWQ0ZGYyYWE4MDdjMyIsImFwcF9uYW1lIjoibGVhbmtpdCIsImF1ZCI6IjE4dWI5bW8wbGRsZ3JzaDNucGNwbXBiOGE4IiwiZXZlbnRfaWQiOiI3MDFkZWZmYy00OWRhLTQ4NDItODI4MC03ZjM4OWM4YjA4YjIiLCJwbGFudmlld19hZG1pbl91cmwiOiJodHRwczpcL1wvdXMuaWQucGxhbnZpZXdsb2dpbmRldi5uZXRcLyIsImFwcF91c2VyX2lkIjoiMTAxMjc4MDY0MzMiLCJwbGF0Zm9ybWFfcm9sZSI6ImFkbWluIiwidG9rZW5fdXNlIjoiaWQiLCJwbGF0Zm9ybWFfYWNjb3VudF9pZCI6ImQwMy0xMDEyNzgwNjQyNiIsInBsYW52aWV3X2Vudl9zZWxlY3RvciI6IkxFQU5LSVR-ZDAzLTEwMTI3ODA2NDI2In0.nrJSJJlZO7V7r8oYTrkGdj4e70F7YgDuVCxK1m5nIOa5uk1m1pRv7YA6--tH1uFLwaEU4YJpvk-JSfOuM4kSoHFPZYLg78S8_qY3pTaFkTLu4cV4pF_37mUd7xhbV2oCjwVCkrNuZ2W3nIN_AU3uDnudOFTSZQVE_NF_AxQC3Az_2rPmvdgS3877caNE5GFxRYMb8eNHIp6ENhKF_BlzajrIOGQnsOxPaIri1wfchjS3eVbK-Ej2tPRn7K3OYRltkl88Rxv2jGgjay_Galwp74ywEnM0GxXT-8H8I8XVjGAiXvjRba1GWsHcd1RHEoeHFMAsT2sjeIgKvrJAa9IUOQ"


@pytest.fixture
def app_domain_pts_token():
    """Return a valid PTS token."""

    return "eyJraWQiOiJcLzhlRVowR0JEdEdUSjc5WkIrSHQ5cTRGSWhYN2tBTE10ZU1DcWJ6ZnRXVT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJodHRwczpcL1wvaGFzdXJhLmlvXC9qd3RcL2NsYWltcyI6IntcIlgtSEFTVVJBLURFRkFVTFQtUk9MRVwiOiBcIm1hbmFnZVwiLCBcIlgtSEFTVVJBLUFMTE9XRUQtUk9MRVNcIjogW1wibWFuYWdlXCJdLCBcIlgtSEFTVVJBLVVTRVItSURcIjogXCIxMDE0NjIzODYwOFwiLCBcIlgtSEFTVVJBLU9SRy1JRFwiOiBcIkxFQU5LSVR-ZDA5LTEwMTEzMjgwODk0XCIsIFwiWC1IQVNVUkEtVEVOQU5ULUdST1VQLUlEXCI6IFwiXCIsIFwiWC1IQVNVUkEtUExBVEZPUk1BLUFQUC1URU5BTlQtSURcIjogXCJMRUFOS0lUfmQwOS0xMDExMzI4MDg5NFwiLCBcIlgtSEFTVVJBLVBMQU5WSUVXLVVTRVItSURcIjogXCJcIiwgXCJYLUhBU1VSQS1QTEFURk9STUEtQVBQLVVTRVItSURcIjogXCIxMDE0NjIzODYwOFwiLCBcIlgtSEFTVVJBLUFQUC1OQU1FXCI6IFwibGVhbmtpdFwifSIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy13ZXN0LTIuYW1hem9uYXdzLmNvbVwvdXMtd2VzdC0yX0VnUjRqeXFpWCIsImFwcF9kb21haW4iOiJkMDkubGVhbmtpdC5pbyIsImNvZ25pdG86dXNlcm5hbWUiOiJwbGF0Zm9ybWEtdXNlciIsImFwcF9jb250ZXh0X2lkIjoiMTAxNDYyNjk2MTYiLCJwbGF0Zm9ybWFfdXNlcl9pZCI6IjEwMTQ2MjM4NjA4IiwiYXBwX25hbWUiOiJsZWFua2l0IiwiYXBwX2NvbnRleHQiOiIiLCJhdWQiOiIxYThlbzNrM2RiNGIzaDk5NnBqMnRxYTUwaSIsInN5c3RlbSI6ImZhbHNlIiwiZXZlbnRfaWQiOiJlNDllMjNiMi1hYjNmLTQyYWItODNkNi1mZTlhZTQ4ODg5ZGUiLCJhcHBfdXNlcl9pZCI6IjEwMTQ2MjM4NjA4IiwicGxhdGZvcm1hX3JvbGUiOiJtYW5hZ2UiLCJ0b2tlbl91c2UiOiJpZCIsInBsYXRmb3JtYV9hY2NvdW50X2lkIjoiTEVBTktJVH5kMDktMTAxMTMyODA4OTQiLCJhdXRoX3RpbWUiOjE2Nzk5MDYwNDQsImFwcF9hY2NvdW50X2lkIjoiMTAxMTMyODA4OTQiLCJleHAiOjE2Nzk5MDk2NDMsImFwcF9yb2xlcyI6ImJvYXJkQWRtaW5pc3RyYXRvciIsImlhdCI6MTY3OTkwNjA0NH0.fJg6LkMLDMb_q3YuLzRmoNES-FhUYBPpTa7-IKL-4oC0Ub5IOXu5C9mhYcG4_yId-cGD7u5nmzTT6hS8UBH_wcgRlL52-iYogmyIr7k4fXiCRr5zFv7IwOj52LR95YTprPqrBT_gc5jTMOjQ3aSbbNBGEufzmp78I55kud4p4L0nc97XQWfn6pHCQF56jGjYORe6WNy_urTay_t1U51H39FbgsMlWF8yFVHHkTjwtPL-KTZMT_jUgX-1p6oX2bhUna4tZJX8yVsZ_qeu4DJ5iHsrOY7hOo3Pc7-s5uq5pwGbFadzYAeRG4-yxza3B-FLFQBsFsrqwQCHYM9bsp7P_Q"


@pytest.fixture
def pvadmin_pts_token():
    """Return a pvamdin settings token."""

    return "eyJraWQiOiJcLzhlRVowR0JEdEdUSjc5WkIrSHQ5cTRGSWhYN2tBTE10ZU1DcWJ6ZnRXVT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJwbGFudmlld191c2VyX2lkIjoiMTMxMjhmOTctZDU4YS00YWI1LTkwYjUtNWM5Njk3YWFmNDE3IiwiaHR0cHM6XC9cL2hhc3VyYS5pb1wvand0XC9jbGFpbXMiOiJ7XCJYLUhBU1VSQS1ERUZBVUxULVJPTEVcIjogXCJtYW5hZ2VcIiwgXCJYLUhBU1VSQS1BTExPV0VELVJPTEVTXCI6IFtcIm1hbmFnZVwiXSwgXCJYLUhBU1VSQS1VU0VSLUlEXCI6IFwiMTMxMjhmOTctZDU4YS00YWI1LTkwYjUtNWM5Njk3YWFmNDE3XCIsIFwiWC1IQVNVUkEtT1JHLUlEXCI6IFwiN2RiODVjZGUtOTVhYy00ZGYxLWEzZDEtMGU5ODYxODBmNmJhOnNiXCIsIFwiWC1IQVNVUkEtVEVOQU5ULUdST1VQLUlEXCI6IFwiN2RiODVjZGUtOTVhYy00ZGYxLWEzZDEtMGU5ODYxODBmNmJhOnNiXCIsIFwiWC1IQVNVUkEtUExBVEZPUk1BLUFQUC1URU5BTlQtSURcIjogXCJcIiwgXCJYLUhBU1VSQS1QTEFOVklFVy1VU0VSLUlEXCI6IFwiMTMxMjhmOTctZDU4YS00YWI1LTkwYjUtNWM5Njk3YWFmNDE3XCIsIFwiWC1IQVNVUkEtUExBVEZPUk1BLUFQUC1VU0VSLUlEXCI6IFwiXCJ9IiwicGxhbnZpZXdfZGVwbG95bWVudF9pZCI6IiIsInBsYW52aWV3X2N1c3RvbWVyX2lkIjoiNDc4MzNhZjgtZWEyYS00NDk3LTk4OTAtNGE5ZDE4OTYxMTJlIiwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLXdlc3QtMi5hbWF6b25hd3MuY29tXC91cy13ZXN0LTJfRWdSNGp5cWlYIiwiY29nbml0bzp1c2VybmFtZSI6InBsYXRmb3JtYS11c2VyIiwicGxhdGZvcm1hX3VzZXJfaWQiOiIiLCJvcmlnaW5fanRpIjoiOGE5MzdjMjMtOTRiOS00NTczLThmYjgtNDJkOGZkMzQ3OTU1IiwiYXVkIjoiNTk2dWIzbWhpYjFhZTZzaGp1bmlvZXEwdmoiLCJzeXN0ZW0iOiJmYWxzZSIsImV2ZW50X2lkIjoiMDhjZDBmZWQtZWZhZi00OGRmLTgyZmEtODA4M2RjZmQxYzM5IiwicGxhbnZpZXdfYWRtaW5fdXJsIjoiaHR0cHM6XC9cL3VzLmlkLnBsYW52aWV3bG9naW5kZXYubmV0XC8iLCJwbGF0Zm9ybWFfcm9sZSI6Im1hbmFnZSIsInRva2VuX3VzZSI6ImlkIiwicGxhbnZpZXdfdGVuYW50X2dyb3VwX2lkIjoiN2RiODVjZGUtOTVhYy00ZGYxLWEzZDEtMGU5ODYxODBmNmJhOnNiIiwicGxhdGZvcm1hX2FjY291bnRfaWQiOiIiLCJhdXRoX3RpbWUiOjE2ODQ0MjUxNTksInBsYW52aWV3X2Vudl9zZWxlY3RvciI6IiIsImV4cCI6MTY4NDQyODc1NywiaWF0IjoxNjg0NDI1MTU5LCJqdGkiOiIyNzgyMTQ5OS1mN2Y5LTRmYzItOTFlYi0xYTBjYzRlODQ2NjkifQ.MEY3_LcGPBhbY1hIHntmdIdBCeI9UiMW0x5De1JubQHjQKhmcNMo7p464yNuiZaniB8uhSGFeilqAEZcoBCZa6VzEah1dOaj4EpWXjqwHsrErgeeFhwTSag_-RJ2Nc9XtNAwHzRiGvtTUVsjhCS_-iUPXrLypc6bNzgjJUAh_hg-Kqm49wSbF90kejyY2tfELhNEi1J7051OglKfqaxUXZEnAYExfc0CmKOYocPLP-XVfKFE8zdB1ADefuDinox-rkH18xzoMnXL4L0h7oUwCydEePQAE4bSIoDjXX1G12sHUyJtruuH65AjRhqiubnJqmXGD0BVLzq_y_ODBgcZsw"


@pytest.fixture
def pvadmin_pts_token_2():
    """Return a pvadmin PTS token with a different user."""

    return "eyJraWQiOiJcLzhlRVowR0JEdEdUSjc5WkIrSHQ5cTRGSWhYN2tBTE10ZU1DcWJ6ZnRXVT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJwbGFudmlld19kZXBsb3ltZW50X2lkIjoiIiwicGxhbnZpZXdfY3VzdG9tZXJfaWQiOiI0NzgzM2FmOC1lYTJhLTQ0OTctOTg5MC00YTlkMTg5NjExMmUiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtd2VzdC0yLmFtYXpvbmF3cy5jb21cL3VzLXdlc3QtMl9FZ1I0anlxaVgiLCJhcHBfZG9tYWluIjoicGxhdGZvcm0tZGV2LWUxLmxlYW5raXQuaW8iLCJhcHBfY29udGV4dF9pZCI6IjEwMTM1Mzc4MTc5IiwicGxhbnZpZXdfcm9sZXMiOiJlZGl0IiwicGxhdGZvcm1hX3VzZXJfaWQiOiIxMDEzNTc1NzU2OCIsImFwcF9jb250ZXh0Ijoie1wiYm9hcmRfaWRcIjpcIjEwMTM1Mzc4MTc5XCJ9IiwicGxhbnZpZXdfdGVuYW50X2dyb3VwX2lkIjoiN2RiODVjZGUtOTVhYy00ZGYxLWEzZDEtMGU5ODYxODBmNmJhOnAiLCJhdXRoX3RpbWUiOjE2OTkyNTMyNjIsImFwcF9hY2NvdW50X2lkIjoiMTAxMjgxMzczMjciLCJleHAiOjE2OTkyNTY4NjIsImFwcF9yb2xlcyI6ImJvYXJkVXNlciIsImlhdCI6MTY5OTI1MzI2MiwicGxhbnZpZXdfdXNlcl9pZCI6IjM1YjRmYmY2LTViNjUtNGU2OS05YTQ2LTJjMjgxZTk0NGQzYiIsImh0dHBzOlwvXC9oYXN1cmEuaW9cL2p3dFwvY2xhaW1zIjoie1wiWC1IQVNVUkEtREVGQVVMVC1ST0xFXCI6IFwiZWRpdFwiLCBcIlgtSEFTVVJBLUFMTE9XRUQtUk9MRVNcIjogW1wiZWRpdFwiXSwgXCJYLUhBU1VSQS1VU0VSLUlEXCI6IFwiMzViNGZiZjYtNWI2NS00ZTY5LTlhNDYtMmMyODFlOTQ0ZDNiXCIsIFwiWC1IQVNVUkEtT1JHLUlEXCI6IFwiN2RiODVjZGUtOTVhYy00ZGYxLWEzZDEtMGU5ODYxODBmNmJhOnBcIiwgXCJYLUhBU1VSQS1URU5BTlQtR1JPVVAtSURcIjogXCI3ZGI4NWNkZS05NWFjLTRkZjEtYTNkMS0wZTk4NjE4MGY2YmE6cFwiLCBcIlgtSEFTVVJBLVBMQVRGT1JNQS1BUFAtVEVOQU5ULUlEXCI6IFwiTEVBTktJVH5kMDMtMTAxMjgxMzczMjdcIiwgXCJYLUhBU1VSQS1QTEFOVklFVy1VU0VSLUlEXCI6IFwiMzViNGZiZjYtNWI2NS00ZTY5LTlhNDYtMmMyODFlOTQ0ZDNiXCIsIFwiWC1IQVNVUkEtUExBVEZPUk1BLUFQUC1VU0VSLUlEXCI6IFwiMTAxMzU3NTc1NjhcIiwgXCJYLUhBU1VSQS1BUFAtTkFNRVwiOiBcImxlYW5raXRcIiwgXCJYLUhBU1VSQS1BUFAtQ09OVEVYVFwiOiBcIntcXFwiYm9hcmRfaWRcXFwiOlxcXCIxMDEzNTM3ODE3OVxcXCJ9XCJ9IiwiY29nbml0bzp1c2VybmFtZSI6InBsYXRmb3JtYS11c2VyIiwiYXBwX25hbWUiOiJsZWFua2l0IiwiYXVkIjoiMWE4ZW8zazNkYjRiM2g5OTZwajJ0cWE1MGkiLCJzeXN0ZW0iOiJmYWxzZSIsImV2ZW50X2lkIjoiYmM4MTI0MDctM2VmYi00YmZiLTlhMzQtOWNjYWFhNzg0YzEyIiwicGxhbnZpZXdfYWRtaW5fdXJsIjoiaHR0cHM6XC9cL3VzLmlkLnBsYW52aWV3bG9naW5kZXYubmV0XC8iLCJhcHBfdXNlcl9pZCI6IjEwMTM1NzU3NTY4IiwicGxhdGZvcm1hX3JvbGUiOiJlZGl0IiwidG9rZW5fdXNlIjoiaWQiLCJwbGF0Zm9ybWFfYWNjb3VudF9pZCI6IkxFQU5LSVR-ZDAzLTEwMTI4MTM3MzI3IiwicGxhbnZpZXdfZW52X3NlbGVjdG9yIjoiTEVBTktJVH5kMDMtMTAxMjgxMzczMjcifQ.p-KbKblnVMH_n734oKeIcQ5YFiiuI3ahb0lJTMwyQwSBCSYmO7qODZGkQLCXc_aS_UVWOTStksjqBmi_3l14nAXzOvF7hI3oJjIUwiCQfV5Zq0uTMU08kUGVPpwml26pk0q5Kep8WQ4-LeNFccDmlw0fC3CxV5dBKkVCYRoQ1dlzynEtrLaJgYsHfYhM0Uzh9zCuMOGz0WzLmAL-lT3Ih66wHiNiQzKeSmMNWHnzmmD98dK0DB-OHu8VD2xdwwLmcwZRqDqWUVV7t31dP3caTtFXEGMrEQBCnNNvwXZmUYREubwhWrh_j048EDtRD7c7c9VSk4ZcGMz9HSKHQvcJxg"


@pytest.fixture
def pvadmin_pts_token_p():
    """Return a pvadmin prod settings token."""

    return "eyJraWQiOiJcLzhlRVowR0JEdEdUSjc5WkIrSHQ5cTRGSWhYN2tBTE10ZU1DcWJ6ZnRXVT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJwbGFudmlld19kZXBsb3ltZW50X2lkIjoiIiwicGxhbnZpZXdfY3VzdG9tZXJfaWQiOiI0NzgzM2FmOC1lYTJhLTQ0OTctOTg5MC00YTlkMTg5NjExMmUiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtd2VzdC0yLmFtYXpvbmF3cy5jb21cL3VzLXdlc3QtMl9FZ1I0anlxaVgiLCJhcHBfZG9tYWluIjoicGxhdGZvcm0tZGV2LWUxLmxlYW5raXQuaW8iLCJhcHBfY29udGV4dF9pZCI6IjEwMTM1OTM2ODQ4IiwicGxhbnZpZXdfcm9sZXMiOiJtYW5hZ2UiLCJwbGF0Zm9ybWFfdXNlcl9pZCI6IjEwMTI4MTU5NjEwIiwiYXBwX2NvbnRleHQiOiIiLCJwbGFudmlld190ZW5hbnRfZ3JvdXBfaWQiOiI3ZGI4NWNkZS05NWFjLTRkZjEtYTNkMS0wZTk4NjE4MGY2YmE6cCIsImF1dGhfdGltZSI6MTY5MzkyMTE4MSwiYXBwX2FjY291bnRfaWQiOiIxMDEyODEzNzMyNyIsImV4cCI6MTY5MzkyNDc4MSwiYXBwX3JvbGVzIjoiYm9hcmRBZG1pbmlzdHJhdG9yIiwiaWF0IjoxNjkzOTIxMTgxLCJwbGFudmlld191c2VyX2lkIjoiMTMxMjhmOTctZDU4YS00YWI1LTkwYjUtNWM5Njk3YWFmNDE3IiwiaHR0cHM6XC9cL2hhc3VyYS5pb1wvand0XC9jbGFpbXMiOiJ7XCJYLUhBU1VSQS1ERUZBVUxULVJPTEVcIjogXCJtYW5hZ2VcIiwgXCJYLUhBU1VSQS1BTExPV0VELVJPTEVTXCI6IFtcIm1hbmFnZVwiXSwgXCJYLUhBU1VSQS1VU0VSLUlEXCI6IFwiMTMxMjhmOTctZDU4YS00YWI1LTkwYjUtNWM5Njk3YWFmNDE3XCIsIFwiWC1IQVNVUkEtT1JHLUlEXCI6IFwiN2RiODVjZGUtOTVhYy00ZGYxLWEzZDEtMGU5ODYxODBmNmJhOnBcIiwgXCJYLUhBU1VSQS1URU5BTlQtR1JPVVAtSURcIjogXCI3ZGI4NWNkZS05NWFjLTRkZjEtYTNkMS0wZTk4NjE4MGY2YmE6cFwiLCBcIlgtSEFTVVJBLVBMQVRGT1JNQS1BUFAtVEVOQU5ULUlEXCI6IFwiTEVBTktJVH5kMDMtMTAxMjgxMzczMjdcIiwgXCJYLUhBU1VSQS1QTEFOVklFVy1VU0VSLUlEXCI6IFwiMTMxMjhmOTctZDU4YS00YWI1LTkwYjUtNWM5Njk3YWFmNDE3XCIsIFwiWC1IQVNVUkEtUExBVEZPUk1BLUFQUC1VU0VSLUlEXCI6IFwiMTAxMjgxNTk2MTBcIiwgXCJYLUhBU1VSQS1BUFAtTkFNRVwiOiBcImxlYW5raXRcIn0iLCJjb2duaXRvOnVzZXJuYW1lIjoicGxhdGZvcm1hLXVzZXIiLCJhcHBfbmFtZSI6ImxlYW5raXQiLCJhdWQiOiIxYThlbzNrM2RiNGIzaDk5NnBqMnRxYTUwaSIsInN5c3RlbSI6ImZhbHNlIiwiZXZlbnRfaWQiOiI0MDRlZjFiNi0wZGY2LTQyYjYtOGI5Yi1kZTE1YTZmMzVhZDUiLCJwbGFudmlld19hZG1pbl91cmwiOiJodHRwczpcL1wvdXMuaWQucGxhbnZpZXdsb2dpbmRldi5uZXRcLyIsImFwcF91c2VyX2lkIjoiMTAxMjgxNTk2MTAiLCJwbGF0Zm9ybWFfcm9sZSI6Im1hbmFnZSIsInRva2VuX3VzZSI6ImlkIiwicGxhdGZvcm1hX2FjY291bnRfaWQiOiJMRUFOS0lUfmQwMy0xMDEyODEzNzMyNyIsInBsYW52aWV3X2Vudl9zZWxlY3RvciI6IkxFQU5LSVR-ZDAzLTEwMTI4MTM3MzI3In0.Mt85ZqLlEpx6bN0ncCdwH7eb72Kk3zfC6uy0na94Q6_hWmREB4PSjwJ7YbZbWLvJp4RiJVK4ux-dWBuGEmFzzHdQ3-xL5DDlUzqQ40OEBV5y0geDdXA7aF5Ut116uMBi5mWvtCKLx-1wXVAXzFFyHdg3HP9IPRnnBy4QB-ud_j4UcHXV8QIog5fDnOT6QyVtItF0dybJC904YRmm2GCR8BJgPpSeCkZMSgcNBpauEmzNu1Az5dBvA95eUa27xiOT5dCkY9PL-Xy3xnhnJmAKtxWfP99oJN-dVgAevKxxTIRyMMEkfu82CYpHMtkMiffc6F6R5fTNEa3u_sNpxd-Ojw"


@pytest.fixture
def pvadmin_pts_read_token():
    """Return a pvamdin settings token."""

    return "eyJraWQiOiJcLzhlRVowR0JEdEdUSjc5WkIrSHQ5cTRGSWhYN2tBTE10ZU1DcWJ6ZnRXVT0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzOTk3ZmM0MS1kMGVjLTRlYWYtODRkMi03YmMzZTIxZjU3MTUiLCJwbGFudmlld19kZXBsb3ltZW50X2lkIjoiIiwicGxhbnZpZXdfY3VzdG9tZXJfaWQiOiI0NzgzM2FmOC1lYTJhLTQ0OTctOTg5MC00YTlkMTg5NjExMmUiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtd2VzdC0yLmFtYXpvbmF3cy5jb21cL3VzLXdlc3QtMl9FZ1I0anlxaVgiLCJhcHBfZG9tYWluIjoicGxhdGZvcm0tZGV2LWUxLmxlYW5raXQuaW8iLCJhcHBfY29udGV4dF9pZCI6IjEwMTM1Mzc4MTc5IiwicGxhbnZpZXdfcm9sZXMiOiJyZWFkIiwicGxhdGZvcm1hX3VzZXJfaWQiOiIxMDEzNTc1NzU1MCIsImFwcF9jb250ZXh0IjoiIiwicGxhbnZpZXdfdGVuYW50X2dyb3VwX2lkIjoiN2RiODVjZGUtOTVhYy00ZGYxLWEzZDEtMGU5ODYxODBmNmJhOnAiLCJhdXRoX3RpbWUiOjE2OTIzMzI2MTgsImFwcF9hY2NvdW50X2lkIjoiMTAxMjgxMzczMjciLCJleHAiOjE2OTIzMzYyMTgsImFwcF9yb2xlcyI6ImJvYXJkUmVhZGVyIiwiaWF0IjoxNjkyMzMyNjE4LCJwbGFudmlld191c2VyX2lkIjoiMWU4Yzc2NDAtMWVkOS00MzdkLWE5ODEtN2U2NGY0MDUxMzZmIiwiaHR0cHM6XC9cL2hhc3VyYS5pb1wvand0XC9jbGFpbXMiOiJ7XCJYLUhBU1VSQS1ERUZBVUxULVJPTEVcIjogXCJyZWFkXCIsIFwiWC1IQVNVUkEtQUxMT1dFRC1ST0xFU1wiOiBbXCJyZWFkXCJdLCBcIlgtSEFTVVJBLVVTRVItSURcIjogXCIxZThjNzY0MC0xZWQ5LTQzN2QtYTk4MS03ZTY0ZjQwNTEzNmZcIiwgXCJYLUhBU1VSQS1PUkctSURcIjogXCI3ZGI4NWNkZS05NWFjLTRkZjEtYTNkMS0wZTk4NjE4MGY2YmE6cFwiLCBcIlgtSEFTVVJBLVRFTkFOVC1HUk9VUC1JRFwiOiBcIjdkYjg1Y2RlLTk1YWMtNGRmMS1hM2QxLTBlOTg2MTgwZjZiYTpwXCIsIFwiWC1IQVNVUkEtUExBVEZPUk1BLUFQUC1URU5BTlQtSURcIjogXCJMRUFOS0lUfmQwMy0xMDEyODEzNzMyN1wiLCBcIlgtSEFTVVJBLVBMQU5WSUVXLVVTRVItSURcIjogXCIxZThjNzY0MC0xZWQ5LTQzN2QtYTk4MS03ZTY0ZjQwNTEzNmZcIiwgXCJYLUhBU1VSQS1QTEFURk9STUEtQVBQLVVTRVItSURcIjogXCIxMDEzNTc1NzU1MFwiLCBcIlgtSEFTVVJBLUFQUC1OQU1FXCI6IFwibGVhbmtpdFwifSIsImNvZ25pdG86dXNlcm5hbWUiOiJwbGF0Zm9ybWEtdXNlciIsImFwcF9uYW1lIjoibGVhbmtpdCIsImF1ZCI6IjFhOGVvM2szZGI0YjNoOTk2cGoydHFhNTBpIiwic3lzdGVtIjoiZmFsc2UiLCJldmVudF9pZCI6ImY1YmE4ZTQwLTNiNTUtNDhmMS1iMGRkLWUzM2VjNTI3YzM5NCIsInBsYW52aWV3X2FkbWluX3VybCI6Imh0dHBzOlwvXC91cy5pZC5wbGFudmlld2xvZ2luZGV2Lm5ldFwvIiwiYXBwX3VzZXJfaWQiOiIxMDEzNTc1NzU1MCIsInBsYXRmb3JtYV9yb2xlIjoicmVhZCIsInRva2VuX3VzZSI6ImlkIiwicGxhdGZvcm1hX2FjY291bnRfaWQiOiJMRUFOS0lUfmQwMy0xMDEyODEzNzMyNyIsInBsYW52aWV3X2Vudl9zZWxlY3RvciI6IkxFQU5LSVR-ZDAzLTEwMTI4MTM3MzI3In0.CVDtyoaWw9XmAONeFpd3jhZkqPYeBnPCm2eEHlJbJ2noobMuQstosHGqiYuVlr1tAMCAFtiCaB1KYM-uotseRsSmNDZj3Pu8lm6U3QuIcuydblcVX9GZmXfhoCk4jFRF8HO75U42NhA83YYLTe8WomEg2jIYZPJTtmJTAZX06trETjNNAva-TAHkBQ9SB_LXJtlVx9AszrZdJR1SCIgtKNVY362IqOhTd8z8lWat6Dx0xLsaPCFXy9NTgZgYVQF53H2h-e9L180quM8f5vjlVjbWlbhOWpno2j59lMeAkJp8mDRsuE3TYntdWTcjOrxUXvG-6SuOEo6G-Nk4yk3kFw"


@pytest.fixture
def request_with_jwt(mocker, connexion_client, dummy_pts_token):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {dummy_pts_token}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_jwt_app_domain(mocker, connexion_client, app_domain_pts_token):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {app_domain_pts_token}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_pvadmin_jwt(mocker, connexion_client, dummy_pts_pvadmin_token):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {dummy_pts_pvadmin_token}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_pvadmin_settings_jwt(
    mocker, connexion_client, dummy_pts_pvadmin_settings_token
):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {dummy_pts_pvadmin_settings_token}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_real_pvadmin_settings_jwt(mocker, connexion_client, pvadmin_pts_token):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {pvadmin_pts_token}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_real_pvadmin_settings_jwt_p(
    mocker, connexion_client, pvadmin_pts_token_p
):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {pvadmin_pts_token_p}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_real_edit_jwt(mocker, connexion_client, pvadmin_pts_read_token):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {pvadmin_pts_read_token}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_real_edit_jwt_2(mocker, connexion_client, pvadmin_pts_token_2):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {pvadmin_pts_token_2}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_jwt_having_admin_url(
    mocker, connexion_client, dummy_pts_token_with_pvadmin_url
):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {dummy_pts_token_with_pvadmin_url}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_jwt_having_admin_url_https(
    mocker, connexion_client, dummy_pts_token_with_pvadmin_url_https
):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {
        "Authorization": f"Bearer {dummy_pts_token_with_pvadmin_url_https}"
    }
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_jwt_having_id_token(
    mocker, connexion_client, dummy_pts_token_with_id_token
):
    """Return a mock request with the Planview Token Service JWT info in the auth."""

    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {dummy_pts_token_with_id_token}"}
    original_settings = connexion_client.app["settings"]
    request.config_dict = {"settings": original_settings}
    request.app = {
        "db_session": UnifiedAlchemyMagicMock(),
        "client_session": connexion_client.session,
    }
    return request


@pytest.fixture
def request_with_pts_jwt(app_settings, request_with_jwt, dummy_pts_token):
    """
    Return a JWT with a PTS token.

    The PTS token supplied here is pulled from the settings.
    Setting `TEST_PLANVIEW_TOKEN_SERVICE_JWT` in your environment will pick this
    token up any other environment other than Local.

    This can be used to make actual working network calls in your local development
    and then use VCR to capture that output.
    """
    pts_token = app_settings.local_test.planview_token_service_jwt or dummy_pts_token
    request_with_jwt.headers = {"Authorization": pts_token}
    return request_with_jwt


@pytest.fixture
def request_with_db_session(request_with_jwt, db_session):
    """Return a mock request with an actual db_session."""
    request_with_jwt.app["db_session"] = db_session
    return request_with_jwt


@pytest.fixture
def event_handler_factory(connexion_client):
    """Return a function to create a handler of a specific type from input data."""

    def _handler_factory(
        handler_klass,
        input_data=None,
        db_session=None,
        client_session=None,
        app_settings=None,
    ):
        """
        Return a handler of the specific class.

        :param class handler_klass: the class of the handler
        :param dict input_data: the input data from Hasura
        :param db_session db_session: (optional) the db_session
        :param client_session client_session: (optional) the client_session
        :param dict app_settings: (optional) the app_settings
        """
        input_data = input_data or {}
        event_parser = EventParser(input_data)
        return handler_klass(
            event_parser=event_parser,
            db_session=db_session or UnifiedAlchemyMagicMock(),
            client_session=client_session or connexion_client.session,
            app_settings=app_settings or connexion_client.app["settings"],
        )

    return _handler_factory


@pytest.fixture
@pytest.mark.usefixtures("init_models")
def create_db_basic_setting(db_session):
    """
    Return a setting that already exists or create one.

    This will use the DEFAULT_TENANT_ID_STR below to look for a setting.
    If the setting already exists, it will return it.
    If it does not find the setting, then it
    will create it, using any parameters passed in.
    """
    default_tenant_id_str = "LEANKIT~d09-10113280894"

    def _create_db_basic_setting(settings_dict=None):
        base_settings = {"tenant_id_str": default_tenant_id_str}
        settings_dict = base_settings | (settings_dict or {})
        tenant_id_str = settings_dict.get("tenant_id_str")
        setting = (
            db_session.query(models.Setting)
            .filter_by(tenant_id_str=tenant_id_str)
            .first()
        )
        if not setting:
            setting = models.Setting(**settings_dict)
            db_session.add(setting)
            db_session.commit()
        return setting

    return _create_db_basic_setting


@pytest.fixture
@pytest.mark.usefixtures("init_models")
def create_work_item_container(db_session, create_db_basic_setting):
    """
    Create a WIC, taking into account triggers.
    """

    DEFAULT_TENANT_ID_STR = "LEANKIT~d12-1234"
    UPDATE_ONLY_ATTRIBS = ["objective_editing_levels", "level_depth_default"]
    BASE_ATTRIBS = {
        "tenant_id_str": DEFAULT_TENANT_ID_STR,
        "external_id": "123",
        "external_type": "leankit",
        "app_name": "leankit",
    }

    def _create_work_item_container(attribs=None):
        """
        Create a WIC, taking into account triggers.

        This will also create a basic_setting as well, or find one that already
        exists for the tenant_id_str.

        There are database triggers that complicate the creation of a simple WIC.
        This fixture will take in the attribs, parse them correctly, and create
        the WorkItemContainer.

        :param dict attribs: the attribs to build the work_item_container from
        """
        attribs = BASE_ATTRIBS | (attribs or {})
        create_db_basic_setting({"tenant_id_str": attribs["tenant_id_str"]})
        update_attribs = {}
        attribs = attribs or {}
        insert_attribs = {}
        for k in attribs:
            if k in UPDATE_ONLY_ATTRIBS:
                update_attribs[k] = attribs[k]
            else:
                insert_attribs[k] = attribs[k]

        wic = models.WorkItemContainer(**insert_attribs)
        db_session.add(wic)
        db_session.commit()

        # If there were "update only" attribs, then we must set those attribs
        # after we have created the wic.
        if update_attribs:
            for k in update_attribs:
                setattr(wic, k, update_attribs[k])

            db_session.add(wic)
            db_session.commit()

        return wic

    return _create_work_item_container


# TODO: Consider moving this to factory boy later.
@pytest.mark.usefixtures("init_models")
@pytest.fixture
def build_okr():
    """Build a full OKR."""
    DEFAULT_TENANT_ID_STR = "LEANKIT~d09-10113280894"

    def _build_okr(tenant_id_str=None, wic=None):
        tenant_id_str = tenant_id_str or DEFAULT_TENANT_ID_STR
        if not wic:
            wic = models.WorkItemContainer(
                external_id="123",
                external_type="leankit",
                external_title="Test Board",
                app_name="leankit",
                tenant_id_str=tenant_id_str,
            )
        key_result = models.KeyResult(
            name="Test Key Result",
            starting_value=1,
            target_value=100,
            tenant_id_str=tenant_id_str,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            progress_points=[
                models.ProgressPoint(
                    value=30,
                    measured_at="2021-04-01",
                    tenant_id_str=tenant_id_str,
                )
            ],
        )
        objective = models.Objective(
            name="Test Objective",
            work_item_container=wic,
            level_depth=0,
            tenant_id_str=tenant_id_str,
            starts_at="2020-01-01",
            ends_at="2025-01-01",
            key_results=[key_result],
        )
        return {
            "objective": objective,
            "key_result": key_result,
            "work_item_container": wic,
        }

    return _build_okr


@pytest.fixture()
def build_level_config():
    """
    Build a level config.

    Set levels and  assign colors loosely derived from the names
    passed in. The number of names passed in determines the number of levels.

    :param list(str) names: the names for the levels
    :param int default_level: level to set as default
    """
    DEFAULT_NAMES = ["Enterprise", "Portfolio", "Program", "Team"]

    def _build_level_config(names=None, default_level_depth=0):
        names = names or DEFAULT_NAMES
        level_config = []
        for i, level_name in enumerate(names):
            hex_repr = base64.b16encode(bytearray(f"{i}{level_name}", "utf-8")).decode()
            color = "{:.6}".format(hex_repr)
            level = {
                "name": level_name,
                "color": f"#{color}",
                "depth": i,
                "is_default": (i == default_level_depth),
            }
            level_config.append(level)

        return level_config

    return _build_level_config


@pytest.fixture()
def mock_input_prepper(mocker, connexion_client):
    """
    Return a mock input_prepper.

    An `input_prepper` is a consolidator for all request data and body data, as
    well as a one-stop shop for client_session and app settings.
    """
    DEFAULT_ORG_ID = "LEANKIT~d12-123"

    def _mock_input_prepper(
        db_session=None,
        org_id=None,
        app_settings=None,
        data=None,
        tenant_group_id=None,
        app_name=None,
    ):
        db_session = db_session or UnifiedAlchemyMagicMock()
        org_id = org_id or DEFAULT_ORG_ID
        data = data or {}
        return mocker.Mock(
            db_session=db_session,
            org_id=org_id,
            tenant_group_id=tenant_group_id,
            app_name=app_name,
            client_session=connexion_client.session,
            app_settings=app_settings or connexion_client.app["settings"],
            input_parser=mocker.Mock(**data),
        )

    return _mock_input_prepper
