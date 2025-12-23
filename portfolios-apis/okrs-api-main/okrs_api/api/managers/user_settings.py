"""Manager class for progress point custom actions."""
from http import HTTPStatus
from okrs_api.model_helpers.user_settings import (
    fetch_user_settings,
    validate_user_settings,
    create_new_user_settings,
    user_settings_response_adapter,
    get_user_settings_response,
    update_user_settings,
)
from okrs_api.utils import adapt_error_for_hasura


class UserSettingsManager:
    """Class to handle the progres point custom actions."""

    def __init__(self, input_prepper=None):
        """Initialize the ProgressPointsManager with input_prepper."""
        self.input_prepper = input_prepper

    def get_user_setting(self):
        """Get User settings."""
        with self.input_prepper.db_session() as db_session:
            record_exists = fetch_user_settings(db_session, self.input_prepper)
            if record_exists:
                return get_user_settings_response(record_exists[0]), HTTPStatus.OK
        return [], HTTPStatus.OK

    def insert_user_setting(self):
        """Insert User Settings."""
        with self.input_prepper.db_session() as db_session:
            record_exists = fetch_user_settings(db_session, self.input_prepper)
            if record_exists:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="Cannot create User setting with given input",
                            error_code="RECORD_ALREADY_EXISTS",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )

            input_data = self.input_prepper.input_parser
            errors = validate_user_settings(input_data)
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)

            user_setting = create_new_user_settings(db_session, self.input_prepper)
            return user_settings_response_adapter(user_setting), HTTPStatus.OK

    def update_user_setting(self):
        """Update user settings."""
        with self.input_prepper.db_session() as db_session:
            records = fetch_user_settings(db_session, self.input_prepper)
            if not records:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="Cannot update User setting with given input",
                            error_code="RECORD_DOES_NOT_EXISTS",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
            user_setting_obj = records[0]
            input_data = self.input_prepper.input_parser
            errors = validate_user_settings(input_data)

            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)

            user_setting = update_user_settings(
                db_session, input_data, user_setting_obj
            )
            return user_settings_response_adapter(user_setting), HTTPStatus.OK

    @staticmethod
    def is_column_enabled(list_view_column_config, column_id, column_type="static"):
        """Check if a column is enabled in the list view configuration."""
        for column_obj in list_view_column_config:
            if (
                column_obj.get("id") == column_id
                and column_obj.get("column_type") == column_type
                and not column_obj.get("hidden", True)
            ):
                return True
        return False
