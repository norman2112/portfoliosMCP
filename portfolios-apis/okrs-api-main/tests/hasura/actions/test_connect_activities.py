"""Test the Activities Connection Creator."""
# pylint: disable=no-member
from unittest.mock import MagicMock

from mock_alchemy.mocking import UnifiedAlchemyMagicMock
import pytest
from open_alchemy import models

from okrs_api import utils
from okrs_api.hasura.actions.auth import JWTParser
from okrs_api.model_helpers.activity_mappings import ActivitiesConnectionCreator

# Sets a random number as a mocked key result id.
MOCK_KR_ID = 14

# The JWT payload is as follows:
# {
#   "iss": "security.platforma.xyz",
#   "iat": 1608489398,
#   "exp": 1923849398,
#   "sub": "1",
#   "app": {
#     "name": "leankit",
#     "user-id": "54321"
#   },
#   "https://hasura.io/jwt/claims": {
#     "x-hasura-allowed-roles": [
#       "user"
#     ],
#     "x-hasura-default-role": "admin",
#     "x-hasura-user-id": "1234567890",
#     "x-hasura-org-id": "123",
#     "x-hasura-custom": "custom-value"
#   }
# }
INCOMING_JWT = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzZWN1cml0eS5wbGF0Zm9ybWEueHl6IiwiaWF0IjoxNjA4NDg5Mzk4LCJleHAiOjE5MjM4NDkzOTgsInN1YiI6IjEiLCJhcHAiOnsibmFtZSI6ImxlYW5raXQiLCJ1c2VyLWlkIjoiNTQzMjEifSwiaHR0cHM6Ly9oYXN1cmEuaW8vand0L2NsYWltcyI6eyJ4LWhhc3VyYS1hbGxvd2VkLXJvbGVzIjpbInVzZXIiXSwieC1oYXN1cmEtZGVmYXVsdC1yb2xlIjoiYWRtaW4iLCJ4LWhhc3VyYS11c2VyLWlkIjoiMTIzNDU2Nzg5MCIsIngtaGFzdXJhLW9yZy1pZCI6IjEyMyIsIngtaGFzdXJhLWN1c3RvbSI6ImN1c3RvbS12YWx1ZSJ9fQ.Mf5Aucj05ndGR6bN1HeE8Iq0JiKuh4OcShIWSsGbeW4"

# The following is the full secret payload, expressed in a Base64-encoded JWT format
# The `key` in this payload is "secret"
SECRET_PAYLOAD = "eyJhdWRpZW5jZSI6IFsiZG92ZXRhaWwiXSwgImNsYWltc19mb3JtYXQiOiAianNvbiIsICJpc3N1ZXIiOiAic2VjdXJpdHkucGxhdGZvcm1hLnh5eiIsICJrZXkiOiAic2VjcmV0IiwgInR5cGUiOiAiSFMyNTYifQ=="


@pytest.fixture
def mocked_request(mocker):
    """Return a mocked request"""
    request = mocker.patch("aiohttp.web.Request")
    request.headers = {"Authorization": f"Bearer {INCOMING_JWT}"}
    settings_mock = mocker.Mock()
    request.config_dict = {"settings": settings_mock}
    request.app = {"db_session": UnifiedAlchemyMagicMock()}
    return request


def make_input_parser(key_result_id=MOCK_KR_ID):
    """Return an input parser for connect_activities data."""
    input_data = {
        "key_result_id": key_result_id,
        "work_item_container": {
            "external_id": "172635761111",
            "external_type": "leankit",
            "external_title": "A board title!",
        },
        "work_items": [
            {
                "item_type": "",
                "planned_start": None,
                "planned_finish": None,
                "title": "Some title 1",
                "external_id": "1012441370",
                "external_type": "leankit",
                "container_type": "lk_board",
                "state": "finished",
            }
        ],
    }
    return utils.Map(**input_data)


@pytest.fixture
def jwt_parser():
    """Return a JWT Parser, using the defaults."""
    return JWTParser(mocked_request.headers)


class TestActivitiesConnectionCreator:
    """Defines the test suite for the ActivitiesConnectionCreator."""

    DEFAULT_LEVEL_CONFIG = [
        {"depth": 0, "name": "Enterprise", "color": "#ba8aa4", "is_default": False},
        {"depth": 1, "name": "Portfolio", "color": "#f87b55", "is_default": False},
        {"depth": 2, "name": "Program", "color": "#8ab98e", "is_default": True},
        {"depth": 3, "name": "Team", "color": "#608eb6", "is_default": False},
    ]

    @pytest.mark.parametrize(
        "input_parser, mapping_kr_id_expected",
        [
            pytest.param(make_input_parser(5), 5, id="key_result_5"),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_connect_mappings_created(self, input_parser, mapping_kr_id_expected):
        """Ensure the mapping is being created correctly on an empty database."""
        db_session = UnifiedAlchemyMagicMock()
        org_id = "123"
        setting = models.Setting(
            level_config=self.DEFAULT_LEVEL_CONFIG, tenant_id_str=org_id
        )
        db_session.add(setting)
        activities_connection_creator = ActivitiesConnectionCreator(
            db_session=db_session,
            input_parser=input_parser,
            org_id=org_id,
            user_id="1234567890",
            tenant_group_id="1234",
            created_by="4321",
        )
        mappings = activities_connection_creator.connect()

        work_item_container = (
            db_session.query(models.WorkItemContainer)
            .filter_by(tenant_id_str=org_id)
            .first()
        )

        assert work_item_container.level_depth_default == 2
        assert len(mappings) == 1
        assert mappings[0].key_result_id == mapping_kr_id_expected

    @pytest.mark.parametrize(
        "input_parser, mapping_id_expected",
        [
            pytest.param(make_input_parser(), 1, id="key_result_work_item_mapping_1"),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_connect_already_existing_mapping(self, input_parser, mapping_id_expected):
        """Ensure it returns the mapping that is already created in the database."""
        db_session = UnifiedAlchemyMagicMock()
        wi_model = models.WorkItem

        mocked_wi_id = 1
        wi_attribs = input_parser.work_items[0]
        mocked_wi = wi_model(**wi_attribs, id=mocked_wi_id)
        mocked_kr_wi_mapping = models.KeyResultWorkItemMapping(
            key_result_id=input_parser.key_result_id,
            work_item=mocked_wi,
            work_item_id=mocked_wi.id,
            id=mapping_id_expected,
        )
        db_session.add(mocked_wi)
        db_session.add(mocked_kr_wi_mapping)

        activities_connection_creator = ActivitiesConnectionCreator(
            db_session=db_session,
            input_parser=input_parser,
            org_id="123",
            user_id="1234567890",
            tenant_group_id="1234",
            created_by="4321",
        )

        mappings = activities_connection_creator.connect()
        first_mapping = mappings[0]
        assert len(mappings) == 1
        assert first_mapping.id == mapping_id_expected
        assert first_mapping.work_item_id == mocked_wi_id

    @pytest.mark.usefixtures("init_models")
    def test_connect_mappings_throws_exception_if_commit_fails(self):
        """Ensure it raises an exception if the commit to the database fails."""
        db_session = UnifiedAlchemyMagicMock()
        mocked_commit = MagicMock()
        mocked_commit.side_effect = Exception()
        db_session.commit = mocked_commit
        activities_connection_creator = ActivitiesConnectionCreator(
            db_session=db_session,
            input_parser=make_input_parser(),
            org_id="123",
            user_id="1234567890",
            tenant_group_id="1234",
            created_by="4321",
        )

        with pytest.raises(Exception):
            activities_connection_creator.connect()

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_no_error_for_existing_wic(self, db_session, create_work_item_container):
        """Ensure that no errors arise if the WIC exists."""
        # Setup the database.
        tenant_id_str = "LEANKIT-d09-1234"
        existing_wic = create_work_item_container(
            {
                "external_type": "leankit",
                "external_id": "172635761111",
                "tenant_id_str": tenant_id_str,
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        key_result = models.KeyResult(
            name="Test Key Result",
            starting_value=20,
            target_value=200,
            tenant_id_str=tenant_id_str,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            objective=models.Objective(
                name="Test Objective",
                work_item_container=existing_wic,
                level_depth=1,
                tenant_id_str=tenant_id_str,
                starts_at="2021-01-01",
                ends_at="2022-01-01",
            ),
        )

        db_session.add(key_result)
        db_session.commit()

        # Begin test.
        creator = ActivitiesConnectionCreator(
            db_session=db_session,
            input_parser=make_input_parser(key_result.id),
            org_id="1234",
            user_id="1234567890",
            tenant_group_id="1234",
            created_by="4321",
        )
        mappings = creator.connect()
        assert isinstance(mappings[0], models.KeyResultWorkItemMapping)
        assert len(mappings) == 1
