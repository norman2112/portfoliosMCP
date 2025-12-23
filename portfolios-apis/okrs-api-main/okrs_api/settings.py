"""Define the application settings."""
import pathlib
from typing import Optional

# pylint: disable=no-name-in-module
from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import DirectoryPath
from pydantic import FilePath
from pydantic import validator


# pylint: disable=too-few-public-methods
#   This class is meant to only store settings.
class Engine(BaseSettings):
    """
    Represent the database engine configuration.

    Engine options are described here:
    https://docs.sqlalchemy.org/en/13/core/engines.html#engine-creation-api
    """

    # Database connection string.
    # https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls
    name_or_url: str

    # If True, the Engine will log all statements as well as a repr() of their
    # parameter lists to the default log handler, which defaults to sys.stdout
    # for output. If set to the string "debug", result rows will be printed to
    # the standard output as well. The echo attribute of Engine can be modified
    # at any time to turn logging on and off; direct control of logging is also
    # available using the standard Python logging module.
    echo: bool = False

    # if True, the connection pool will log informational output such as when
    # connections are invalidated as well as when connections are recycled to
    # the default log handler, which defaults to sys.stdout for output. If set
    # to the string "debug", the logging will include pool checkouts and
    # checkins. Direct control of logging is also available using the standard
    # Python logging module.
    echo_pool: bool = False

    # boolean,
    # if True will enable the connection pool “pre-ping” feature that tests
    # connections for liveness upon each checkout. This is also known as
    # "pessimistic disconnect handling".
    # https://docs.sqlalchemy.org/en/13/core/pooling.html#disconnect-handling-pessimistic
    pool_pre_ping: bool = True

    # Boolean, when set to True, SQL statement parameters will not be displayed
    # in INFO logging nor will they be formatted into the string representation
    # of StatementError objects.
    hide_parameters: bool = False

    class Config:
        """Control the behavior of the engine settings."""

        fields = {"name_or_url": {"env": "DATABASE_URL"}}


# pylint: disable=too-few-public-methods
#   This class is meant to only store settings.
class Session(BaseModel):
    """
    Represent the database session configuration.

    Session options are described here:
    https://docs.sqlalchemy.org/en/13/orm/session_api.html#sqlalchemy.orm.session.Session
    """

    # !!! Warning !!!
    # The autocommit flag is not for general use, and if it is used, queries
    # should only be invoked within the span of a
    # Session.begin() / Session.commit() pair. Executing queries outside of a
    # demarcated transaction is a legacy mode of usage, and can in some cases
    # lead to concurrent connection checkouts.
    # When True, the Session does not keep a persistent transaction running,
    # and will acquire connections from the engine on an as-needed basis,
    # returning them immediately after their use. Flushes will begin and commit
    # (or possibly rollback) their own transaction if no transaction is present.
    # When using this mode, the Session.begin() method is used to explicitly
    # start transactions.
    autocommit: bool = False

    # When True, all query operations will issue a Session.flush() call to this
    # Session before proceeding. This is a convenience feature so that
    # Session.flush() need not be called repeatedly in order for database
    # queries to retrieve results. It’s typical that autoflush is used in
    # conjunction with autocommit=False. In this scenario, explicit calls to
    # Session.flush() are rarely needed; you usually only need to call
    # Session.commit() (which flushes) to finalize changes.
    # Default is True.
    autoflush: bool = True

    # When True, all instances will be fully expired after each commit(), so
    # that all attribute/object access subsequent to a completed transaction
    # will load from the most recent database state.
    expire_on_commit: bool = True


# pylint: disable=too-few-public-methods
#   This class is meant to only store settings.
class Database(BaseModel):
    """Represent the database configuration."""

    engine: Optional[Engine]
    session: Optional[Session] = Session()


# pylint: disable=too-few-public-methods
#   This class is meant to only store settings.
class LeanKitApi(BaseSettings):
    """Represent the LeanKit API configuration."""

    api_base_domain: Optional[str] = "leankit.io"  # pylint: disable=E1136
    jwt_secret: Optional[str]  # pylint: disable=E1136

    class Config:
        """
        Control the behaviour of the Setting instance.

        Available options are defined here:
        https://pydantic-docs.helpmanual.io/usage/model_config/
        """

        fields = {
            "api_base_domain": {"env": "LK_API_BASE_DOMAIN"},
            "jwt_secret": {"env": "LK_JWT_SECRET"},
        }


# pylint: disable=too-few-public-methods
#   This class is meant to only store settings.
class IntegrationHubApi(BaseSettings):
    """Define the LeanKit API configuration."""

    # Integration Hub Domain
    domain: Optional[str] = "platforma.pvintegrations-dev.net"  # pylint: disable=E1136
    admin_domain: Optional[  # pylint: disable=E1136
        str
    ] = "platforma.pvintegrations-dev.net"
    client_id: Optional[str]  # pylint: disable=E1136
    client_secret: Optional[str]  # pylint: disable=E1136
    admin_client_id: Optional[str]  # pylint: disable=E1136
    admin_client_secret: Optional[str]  # pylint: disable=E1136
    lk_env: Optional[str] = "d08"  # pylint: disable=E1136

    class Config:
        """
        Control the behaviour of the Setting instance.

        Available options are defined here:
        https://pydantic-docs.helpmanual.io/usage/model_config/
        """

        fields = {
            "domain": {"env": "IH_DOMAIN"},
            "admin_domain": {"env": "ADMIN_IH_DOMAIN"},
            "client_id": {"env": "IH_CLIENT_ID"},
            "client_secret": {"env": "IH_CLIENT_SECRET"},
            "admin_client_id": {"env": "IH_ADMIN_CLIENT_ID"},
            "admin_client_secret": {"env": "IH_ADMIN_CLIENT_SECRET"},
            "lk_env": {"env": "LK_ENV"},
        }


# pylint: disable=unsubscriptable-object
class Gunicorn(BaseSettings):
    """Define the gunicorn settings."""

    port: Optional[int] = 8000
    log_level: Optional[str] = "debug"
    timeout: Optional[int] = 1800
    workers: Optional[int] = 5
    reload: Optional[bool] = False
    access_log: Optional[str] = "-"
    access_logformat: Optional[
        str
    ] = '%a %t "%r" %s %b %Tf "%{Referer}i" "%{User-Agent}i"'

    class Config:
        """Config options for this settings class."""

        env_prefix = "gunicorn_"


class LocalTest(BaseSettings):
    """Define the settings only available when testing locally."""

    planview_token_service_jwt: Optional[str]

    class Config:
        """Config options for this settings class."""

        env_prefix = "test_"


class Settings(BaseSettings):
    """Define the base settings for the application."""

    # Name of the application.
    app_name: str = "okrs_api"

    # Port to listen to.
    port: int = 8000

    # Toggle debug mode.
    debug: bool = False

    # Application root directory.
    root_dir: DirectoryPath = pathlib.Path(".").resolve()

    # OpenAPI specifications directory.
    specification_dir: DirectoryPath = "openapi"

    # OpenAPI specfication file path.
    specification_file: FilePath = "openapi.yml"

    # Connexion resolver parameters.
    resolver_module_name = f"{app_name}.api.controller"

    # Database configuration.
    database = Database()

    # Region
    region: str = "us-west-2"

    # Transaction sampling rate for Sentry
    sentry_traces_sample_rate: str = "0.05"

    # LeanKit Configuration
    leankit = LeanKitApi()

    # Integration Hub Configuration
    integration_hub = IntegrationHubApi()

    # Gunicorn Configuration
    gunicorn = Gunicorn()

    # Log level
    log_level = "INFO"

    # pylint: disable=no-self-argument
    @validator("specification_dir", pre=True)
    def apply_root(cls, v, values):
        """Append path to the root directory."""
        return values.get("root_dir") / v

    # pylint: disable=no-self-argument
    @validator("specification_file", pre=True)
    def apply_specification_dir(cls, v, values):
        """Append path to the specification directory."""
        return values.get("specification_dir") / v

    class Config:
        """
        Control the behaviour of the Setting instance.

        Available options are defined here:
        https://pydantic-docs.helpmanual.io/usage/model_config/
        """

        fields = {
            "region": {"env": "AWS_REGION"},
        }


class Local(Settings):
    """Represent the local settings."""

    # Use to test external api calls in local environment.
    test_planview_token_service_jwt: Optional[str]

    log_level = "DEBUG"

    gunicorn = Gunicorn(reload=True, workers=1)

    local_test = LocalTest()


class Docker(Settings):
    """Represent the local settings."""

    # Use to test external api calls in local environment.
    test_planview_token_service_jwt: Optional[str]

    log_level = "DEBUG"

    gunicorn = Gunicorn(reload=True, workers=1)

    local_test = LocalTest()


class Development(Settings):
    """Represent the development settings."""


class Minikube(Settings):
    """Represent the Minikube settings."""


class Staging(Settings):
    """Represent the staging settings."""


class Production(Settings):
    """Represent the production settings."""


def get(environment):
    """Retrieve the application settings."""
    # pylint: disable=unnecessary-lambda
    settings = {
        "local": lambda: Local(
            database=Database(engine=Engine(echo=True), session=Session())
        ),
        "docker": lambda: Docker(
            root_dir="/usr/src/app/",
            database=Database(engine=Engine(echo=True), session=Session()),
        ),
        "development": lambda: Development(
            root_dir="/usr/src/app/",
            database=Database(engine=Engine(), session=Session()),
        ),
        "minikube": lambda: Minikube(
            root_dir="/usr/src/app/",
            database=Database(engine=Engine(), session=Session()),
        ),
        "staging": lambda: Staging(
            root_dir="/usr/src/app/",
            database=Database(engine=Engine(), session=Session()),
        ),
        "production": lambda: Production(
            root_dir="/usr/src/app/",
            database=Database(engine=Engine(), session=Session()),
        ),
        "testing": lambda: Settings(),
    }
    try:
        return settings[environment.lower()]()
    except LookupError as e:
        raise NotImplementedError(f"no settings available for {environment}") from e
