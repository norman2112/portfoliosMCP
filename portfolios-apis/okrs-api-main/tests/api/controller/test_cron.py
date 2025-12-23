"""Test cron endpoints."""

from http import HTTPStatus

from open_alchemy import models
import pytest

from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from okrs_api.api.controller import cron
from okrs_api.model_helpers.common import find_or_build


class TestWorkItemContainerOrphanDeletion:
    @pytest.fixture
    def create_wic(self, mocker, create_db_basic_setting):
        def _create_wic(
            db_session, expired=True, with_objective=None, with_work_item=None
        ):
            tenant_id_str = "LEANKIT~d06-123999"
            if not isinstance(db_session, UnifiedAlchemyMagicMock):
                create_db_basic_setting({"tenant_id_str": tenant_id_str})

            wic = models.WorkItemContainer(
                external_id="987654543787",
                external_type="leankit",
                tenant_id_str=tenant_id_str,
            )
            if expired:
                # We cannot set the `updated_at` field manually; it will be
                # overridden by a trigger. So we must mock out a fake expiration
                # date, pretending that we're actually in the future.
                mocker.patch(
                    "okrs_api.api.controller.cron.WIC_CONTAINER_EXPIRATION_DAYS", -1
                )

            if with_objective:
                wic.objectives = [
                    models.Objective(
                        name="Test Objective",
                        level_depth=3,
                        tenant_id_str=tenant_id_str,
                        starts_at="2021-01-01",
                        ends_at="2025-01-01",
                    )
                ]

            if with_work_item:
                wic.work_items = [
                    models.WorkItem(
                        external_id="287160987",
                        external_type="leankit",
                        tenant_id_str=tenant_id_str,
                    )
                ]

            db_session.add(wic)
            db_session.commit()
            return wic.id

        return _create_wic

    @pytest.mark.parametrize(
        "creation_kwargs, expect_deletion",
        [
            pytest.param({}, True, id="orphaned-wic"),
            pytest.param({"expired": False}, False, id="not-expired-orphan-wic"),
            pytest.param({"with_objective": True}, False, id="has-objective"),
            pytest.param({"with_work_item": True}, False, id="has-work-item"),
            pytest.param(
                {"with_work_item": True, "with_objective": True}, False, id="has-both"
            ),
        ],
    )
    @pytest.mark.integration
    async def test_delete_work_item_container_orphans(
        self, db_session, request_with_jwt, create_wic, creation_kwargs, expect_deletion
    ):
        # Setup database.
        request_with_jwt.app["db_session"] = db_session
        wic_id = create_wic(db_session=db_session, **creation_kwargs)

        # Execute code
        response, status = await cron.delete_work_item_container_orphans(
            request=request_with_jwt, body={}
        )

        # Query for Wic
        found_wic = db_session.query(models.WorkItemContainer).get(wic_id)

        if expect_deletion:
            assert not found_wic
        else:
            assert found_wic

        assert status == HTTPStatus.OK
