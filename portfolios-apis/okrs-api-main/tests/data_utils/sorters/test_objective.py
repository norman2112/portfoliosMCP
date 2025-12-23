"""Test the objective sorter, used for export."""

import pytest

from okrs_api.data_utils.sorters.objective import objective_sorter

from open_alchemy import models


@pytest.fixture
def objective_chain(objective_factory):
    """Return a 4 level objective chain."""
    objective_d0 = objective_factory(name="d0", level_depth=0)
    objective_d1 = objective_factory(
        name="d1", level_depth=1, parent_objective=objective_d0
    )
    objective_d2 = objective_factory(
        name="d2", level_depth=2, parent_objective=objective_d1
    )
    objective_factory(name="d3", level_depth=3, parent_objective=objective_d2)
    return objective_d0


@pytest.mark.integration
def test_objective_order(db_session, objective_chain, setting_factory):
    """
    Test that objectives are returned in an insertable order.

    This means that parent objective must be inserted before their
    child objectives can be.
    """
    setting_factory()
    db_session.commit()

    objectives = (
        db_session.query(models.Objective)
        .filter_by(tenant_id_str=objective_chain.tenant_id_str)
        .all()
    )

    # We reverse the objectives to ensure that we are truly sorting them.
    objectives.reverse()

    sort_list = objective_sorter(objectives)
    sort_list_names = [objective.name for objective in sort_list]
    assert sort_list
    assert sort_list_names == ["d0", "d1", "d2", "d3"]
