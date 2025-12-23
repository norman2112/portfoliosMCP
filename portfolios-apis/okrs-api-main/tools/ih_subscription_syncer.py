"""Re-subscribe work items that have not been subscribed yet."""
# pylint: disable=no-member
# pylint: disable=E0401
import asyncio
from dataclasses import dataclass
import os
from pathlib import Path

from aiohttp import ClientSession
from loguru import logger
from open_alchemy import models
from open_alchemy import init_yaml
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
import sqlalchemy
from sqlalchemy import orm

from okrs_api import settings
from okrs_api.model_helpers.common import dictify_model
from okrs_api.integration_hub.auth import TokenFetcher
from okrs_api.integration_hub.registrations import RegistrationManager
from okrs_api.integration_hub.subscriptions import ActivitySubscriptionManager

ALLOWED_ENVIRONMENTS = ["staging", "production"]
OPENAPI_SPEC_FILE = Path("../openapi/openapi.yml")


@dataclass()
class AppSettings:
    """Reconstituted settings for this script only."""

    @property
    def region(self):
        """Return the region, retrieved from the environment."""
        return os.getenv("AWS_REGION")

    @property
    def integration_hub(self):
        """Return the integration hub settings."""
        return settings.IntegrationHubApi()


def _grouped_work_items(db_session):
    """
    Return work items without subscriptions.

    Group them by tenant code, extracted from `tenant_id_str`.
    """

    work_items = (
        db_session.query(models.WorkItem)
        .filter_by(ih_subscription_response=None)
        .filter(models.WorkItem.tenant_id_str is not None)
        .all()
    )
    # .filter(models.WorkItem.tenant_id_str != None)
    grouped_items = {}
    for wi in work_items:
        tenant_code = wi.tenant_id_str.split("~")[-1]
        if tenant_code not in grouped_items.keys():
            grouped_items[tenant_code] = []

        grouped_items[tenant_code].append(wi)

    return grouped_items


def write_subscription_response(db_session, work_item_id, response_data):
    """Write the Integration Hub subscription response."""
    db_session.query(models.WorkItem).filter(models.WorkItem.id == work_item_id).update(
        {"ih_subscription_response": response_data}
    )
    db_session.commit()


def log_subscription_response(response_data):
    """Log the Integration Hub subscription response."""
    # Log the successful response
    logger.info(f"Integration Hub subscription response = {str(response_data)}")


def initialize_sentry():
    """
    Initialize Sentry for error reporting.

    Details here:
    https://sentry.io/
    https://docs.sentry.io/platforms/python/performance/
    """

    env_str = os.getenv("CONNEXION_ENVIRONMENT")
    if env_str in ALLOWED_ENVIRONMENTS:
        sentry_sdk.init(
            integrations=[AioHttpIntegration()],
            environment=env_str,
            traces_sample_rate=1,
        )


async def main():
    """
    Add subscriptions to work items that do not have them.

    WorkItems are deemed not to have subscriptions if their
    `ih_subscription_response` column is blank.
    """

    # Load the models.
    init_yaml(OPENAPI_SPEC_FILE)

    app_settings = AppSettings()

    # Connect to the database.
    db = sqlalchemy.create_engine(os.environ["DATABASE_URL"])
    db_session = orm.scoped_session(orm.sessionmaker(bind=db))

    # Get all WorkItems, grouped by tenant code.
    grouped_items = _grouped_work_items(db_session)

    if grouped_items:
        logger.info(
            "[subscription syncer] Re-doing subscriptions for "
            f"{len(grouped_items)} work items"
        )
    else:
        logger.info(
            "[subscription syncer] No unsubscribed work items found. Cancelling."
        )
        return

    # Start a client session
    async with ClientSession() as client_session:
        # 1. Fetch the auth token for IH.
        token_fetcher = TokenFetcher(client_session, app_settings)
        bearer_token = await token_fetcher.fetch_token()

        # 2. For each tenant code, register our adapter and get
        # back a global tenant id.
        for tenant_code, work_items in grouped_items.items():
            registration_manager = RegistrationManager(
                client_session=client_session,
                app_settings=app_settings,
                bearer_token=bearer_token,
                tenant_parser=tenant_code,
            )

            if not await registration_manager.register():
                raise Exception("Could not register with Integration Hub.")

            global_tenant_id = registration_manager.response_data.global_tenant_id

            # 3. Use the global tenant id to make subscriptions for each work item.
            for work_item in work_items:
                work_item_attribs = dictify_model(
                    work_item,
                    ["id", "external_type", "external_id", "tenant_id_str"],
                )

                subscription_manager = ActivitySubscriptionManager(
                    client_session=client_session,
                    work_item_attribs=work_item_attribs,
                    app_settings=app_settings,
                    bearer_token=bearer_token,
                    global_tenant_id=global_tenant_id,
                    tenant_parser=tenant_code,
                )

                await subscription_manager.subscribe()

                log_subscription_response(
                    response_data=subscription_manager.response_data
                )
                if subscription_manager.response.ok:
                    write_subscription_response(
                        db_session=db_session,
                        work_item_id=work_item_attribs["id"],
                        response_data=subscription_manager.response_data,
                    )
                else:
                    raise Exception(f"Could not subscribe for work item {work_item.id}")


if __name__ == "__main__":
    asyncio.run(main())
