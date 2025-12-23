"""Define planter module."""
# pylint: disable=no-member
import os
from pathlib import Path
import random
import uuid
import datetime

from faker import Faker
from faker_planview.okr_provider import OKRProvider
from open_alchemy import init_yaml
from open_alchemy import models
import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy import orm

from tools.seeder import activity_logs


# Create the faker and register the extensions.
fake = Faker()
fake.add_provider(OKRProvider)

OPENAPI_SPEC_FILE = Path("../openapi/openapi.yml")

TRACKABLE_COLUMNS = {"objectives": "objective_id", "key_results": "key_result_id"}
PRODUCT_TYPES = ["leankit"]

STATES = ["not_started", "in_progress", "finished"]

MAXIMUM_OBJECTIVES_PER_CONTAINER = 3
MAXIMUM_CONTAINERS_PER_SPACE = 5
MAXIMUM_PROGRESS_POINTS = 10
MAXIMUM_PROGRESS_POINT_VALUE = 100
MINIMUM_WORK_ITEMS = 5
MAXIMUM_WORK_ITEMS = 10
MINIMUM_ITEM = 1
DEFAULT_OBJECTIVE_LEVEL_DEPTH = 3
DEFAULT_STARTS_AT = datetime.datetime.now() - datetime.timedelta(days=365)
DEFAULT_ENDS_AT = datetime.datetime.now() + datetime.timedelta(days=365)

TENANT_ID_STR = "LEANKIT~d09-10113280894"
USER_IDS = ["10145734214", "10145734719"]


def pick_user_id():
    """Pick a user id from the available USER_IDS."""
    return random.choice(USER_IDS)


def set_default_attributes(instance):
    """Set default attributes on an instance."""
    instance.tenant_id_str = TENANT_ID_STR
    instance.app_created_by = pick_user_id()
    instance.app_last_updated_by = pick_user_id()
    return instance


def fake_work_item_factory():
    """
    Generate a Fake Work Item (TEMPORARY).

    This takes the `fake.work_item()` output and replaces the `workable`
    keys with `external` ones.

    This is TEMPORARY workaround until the faker planview okr provider
    is changed over to use "external_id" and "external_type" instead of
    "workable_id" and "workable_type".
    """
    wi = fake.work_item()
    if "workable_id" in wi:
        wi["external_id"] = wi.pop("workable_id")
        wi["external_type"] = wi.pop("workable_type")
    return wi


class ContainerFactory:
    """Build the appropriate number of Work Item Containers."""

    def __init__(self):
        """
        Initialize values for the factory.

        Tally the objective count by how many times this factory has been
        initialized.
        """
        self.max_objective_count = random.randint(
            MINIMUM_ITEM, MAXIMUM_OBJECTIVES_PER_CONTAINER
        )
        self.current_objective_count = 0
        self.current_container = None

    def build_or_reuse_container(self):
        """Generate the container or returns a non-full container."""
        if self.current_container:
            return self.current_container

        self.current_container = self._build_container()
        self.current_objective_count += 1
        return self.current_container

    @property
    def is_full(self):
        """Return True If the container has the requisite number of objectives."""
        return self.current_objective_count >= self.max_objective_count

    def _build_container(self):
        external_id = uuid.uuid4()
        return models.WorkItemContainer(
            external_type=random.choice(PRODUCT_TYPES),
            external_id=external_id,
            external_title=f"Test Container {external_id}",
        )


def add_all(db_session, entities, refresh=False):
    """
    Insert all the entities in the database and refresh the objects.

    :param db_session: the database session
    :param list entities: the list of entities to persist into the database
    :param bool refresh: if `True`, the entities will be expired and refreshed.
    """
    for e in entities:
        set_default_attributes(e)
    db_session.add_all(entities)
    db_session.commit()
    if not refresh:
        return
    for entity in entities:
        db_session.refresh(entity)


# pylint: disable=too-many-locals
#   Since it is a scripts, this is bound to happen.
def main():  # noqa: C901
    """Define the main entrypoint of the program."""
    # Load the models.
    init_yaml(OPENAPI_SPEC_FILE)

    # Connect to the database.
    db = sqlalchemy.create_engine(os.environ["DATABASE_URL"])
    db_session = orm.scoped_session(orm.sessionmaker(bind=db))

    # Delete existing tables content.
    metadata = MetaData()
    metadata.reflect(bind=db)
    for table in reversed(metadata.sorted_tables):
        if table.name != "alembic_version":
            db_session.execute(f"truncate table {table.name} restart identity cascade")
    db_session.commit()

    # Generate fake objectives-key-results.
    objectives_ = fake.okr(-1)

    # Create settings record
    settings = []
    settings.append(models.Setting())
    add_all(db_session, settings, refresh=True)

    # Create objectives and work item containers
    work_item_containers = []
    wic_factory = ContainerFactory()
    objectives = []
    key_results = []
    for objective in objectives_:
        if wic_factory.is_full:
            wic_factory = ContainerFactory()
        container = wic_factory.build_or_reuse_container()
        work_item_containers = [
            set_default_attributes(work_item_container)
            for work_item_container in work_item_containers
        ]
        if container not in work_item_containers:
            work_item_containers.append(container)

        # Create the key-results for this objective.
        krs = [models.KeyResult(**kr) for kr in objective["key_results"]]
        key_results += krs
        key_results = [set_default_attributes(key_result) for key_result in key_results]

        # Create the objective and associate the key-results.
        objectives.append(
            models.Objective(
                name=objective["name"],
                work_item_container=container,
                key_results=krs,
                level_depth=3,
                starts_at=DEFAULT_STARTS_AT,
                ends_at=DEFAULT_ENDS_AT,
            )
        )
    work_item_containers = [
        set_default_attributes(work_item_container)
        for work_item_container in work_item_containers
    ]
    add_all(db_session, objectives, refresh=True)
    for row in work_item_containers:
        row.objective_editing_levels = [0, 1, 2, 3]
    add_all(db_session, work_item_containers, refresh=True)

    # associate parent_objective_ids for objectives
    for objective in objectives:
        objective.level_depth = random.randint(0, 3)
        if objective.level_depth > 0:
            for o in objectives:
                if o.level_depth < objective.level_depth:
                    objective.parent_objective_id = o.id
                    break

    # Create progress points.
    progress_points = [
        models.ProgressPoint(
            value=value,
            key_result=kr,
            measured_at=(kr.starts_at + datetime.timedelta(days=index)),
        )
        for kr in key_results
        for index, value in enumerate(fake.progress_points(), start=1)
    ]
    add_all(db_session, progress_points)

    # Create work items.
    work_items = [
        models.WorkItem(
            # TODO: replace this with **fake.work_item() once changes have
            # been made in faker-planview. -eric 2020/12/17
            **fake_work_item_factory(),
            work_item_container_id=wic.id,
        )
        for wic in work_item_containers
        for _ in range(random.randrange(MINIMUM_WORK_ITEMS, MAXIMUM_WORK_ITEMS))
    ]
    add_all(db_session, work_items)

    # Create key result work item mapping.
    work_item_ids = [work_item.id for work_item in work_items]
    key_result_work_item_mappings = [
        models.KeyResultWorkItemMapping(
            key_result_id=key_result.id,
            work_item_id=work_item_id,
        )
        for key_result in key_results
        for work_item_id in sorted(
            random.sample(work_item_ids, random.randint(1, len(work_item_ids)))
        )
    ]
    add_all(db_session, key_result_work_item_mappings)

    # Add activity logs
    activity_logs.seed(db_session)


if __name__ == "__main__":
    main()
