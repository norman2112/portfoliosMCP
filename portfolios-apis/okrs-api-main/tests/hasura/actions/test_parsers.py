from okrs_api import utils


class TestInputParser:
    """Ensure the input parser factory assigns attributes properly."""

    BASE_INPUT_DATA = {
        "context_id": "12345",
        "product_type": "leankit",
        "domain": "d08.leankit.io",
    }

    def test_input_parser_attribute_setting(self):
        """Ensure input_parser sets attributes for dot notation."""

        input_data = {
            **self.BASE_INPUT_DATA,
            "search_string": "Good Test",
        }
        parser = utils.Map(**input_data)

        # Still works as a normal parser.
        assert parser.product_type == "leankit"

        # adds allowed attributes and assigned their value.
        assert parser.search_string == "Good Test"

        # ensure that allowed attributes without values in the data are still available
        assert parser.limit == None
