import pytest

from okrs_api.hasura.events.event_parser import EventParser
from tests.hasura.events.payloads import event_payload


class TestEventParser:
    @pytest.fixture
    def test_payload(self):
        return {
            "event": {
                "op": "UPDATE",
                "data": {
                    "new": {
                        "animal": "Dog",
                        "pet_me": "yes",
                        "barking": 10,
                    },
                    "old": {
                        "animal": "Cat",
                        "pet_me": "Not so fast",
                        "meowing": 10,
                    },
                },
            },
            "trigger": {"name": "test_update"},
            "table": {"name": "progress_points"},
        }.copy()

    @pytest.mark.parametrize(
        "keys, expected",
        [
            pytest.param(["animal"], {"animal": "Dog"}, id="one-key"),
            pytest.param(
                ["animal", "pet_me"],
                {"animal": "Dog", "pet_me": "yes"},
                id="multiple-keys",
            ),
            pytest.param(
                ["animal", "meowing"], {"animal": "Dog", "meowing": 10}, id="mixed-keys"
            ),
        ],
    )
    def test_subset_data(self, test_payload, keys, expected):
        """Ensure that we return a subset of the data."""
        parser = EventParser(test_payload)
        assert parser.subset_data(keys) == expected
        assert parser.operation == "update"

    @pytest.mark.parametrize(
        "changes, expected",
        [
            pytest.param(
                {"animal": "Giraffe", "barking": 0},
                {"animal": "Giraffe", "pet_me": "yes", "barking": 0},
                id="animal-change",
            ),
            pytest.param(
                {}, {"animal": "Dog", "pet_me": "yes", "barking": 10}, id="no-change"
            ),
        ],
    )
    def test_writeback(self, test_payload, changes, expected):
        """Ensure that data is written back correctly to the event parser."""
        parser = EventParser(test_payload)
        result = parser.writeback(changes)
        assert result == expected
        assert parser.new_data == expected

    def test_proper_update_detection(self):
        """Ensure that a update operation is not confused for a soft delete."""
        payload = event_payload(table="objectives", operation="update")
        parser = EventParser(payload)
        assert parser.operation == "update"

    def test_soft_delete_detection(self, objective_factory):
        """Ensure that a update operation is not confused for a soft delete."""
        objective = objective_factory.build(deleted_at_epoch=999999)
        payload = event_payload(
            table="objectives", operation="update", model_instance=objective
        )
        parser = EventParser(payload)
        assert parser.operation == "delete"

    def test_changed_attribs(self):
        """Ensure changed attribs are correct."""
        payload = event_payload(table="objectives", operation="update")
        parser = EventParser(payload)
        changed_attribs = parser.changed_attribs
        assert "deleted_at_epoch" not in changed_attribs
        assert "Stand down" in changed_attribs["name"]
