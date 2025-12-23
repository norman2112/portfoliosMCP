"""The base validation functions."""

from okrs_api.validators.errors import ValidationError


class BaseValidator:
    """
    The Base validator for all other Validators.

    Validators are designed to validate incoming requests. So they will take in
    the request params and body of the incoming request.
    """

    VALIDATIONS = []

    def __init__(self, input_prepper):
        """Initialize the Validators."""
        self.input_prepper = input_prepper
        self.errors = []

    def validate(self):
        """
        Validate the level config.

        Pull all validation function names and run them.
        All validations:
        - are private methods
        - end in '_check'
        - return `True` if valid and `False` if not
        - append to the errors array if `False`

        This returns True or False, based on the existence of errors.
        """
        # Reset the errors.
        self.errors = []
        for vfunc_name in self.VALIDATIONS:
            getattr(self, f"_{vfunc_name}_check")()

        return not self.errors

    @property
    def error_message(self):
        """Return all error messages concatenated."""
        return " ".join(error.message for error in self.errors)

    @property
    def serializable_errors(self):
        """Return the errors as dicts."""
        return [error.to_dict() for error in self.errors]

    @property
    def input_parser(self):
        """Return the input parser from the input prepper."""
        return self.input_prepper.input_parser

    @property
    def db_session(self):
        """Return the database session."""
        return self.input_prepper.db_session

    @property
    def app_settings(self):
        """Return the app settings."""
        return self.input_prepper.app_settings

    @property
    def client_session(self):
        """Return the client session."""
        return self.input_prepper.client_session

    @property
    def org_id(self):
        """Return the org id."""
        return self.input_prepper.org_id

    @property
    def tenant_group_id(self):
        """Return the tenant group id."""
        return self.input_prepper.tenant_group_id

    @property
    def app_name(self):
        """Return the app name."""
        return self.input_prepper.app_name

    @property
    def planview_user_id(self):
        """Return the planview user id."""
        return self.input_prepper.planview_user_id

    @property
    def user_id(self):
        """Return the user id."""
        return self.input_prepper.user_id

    def add_error(self, code, message, details=None):
        """
        Append an error message.

        :param str code: the error code for the error
        :param str message: the message for the error
        :param [dict] details: interpolation objects with attribute/value

        The details are available for outside apps to use for interpolation,
        if they so wish to do so.
        """
        self.errors.append(ValidationError(code=code, message=message, details=details))

    def append_errors(self, errors):
        """Append a list of errors into the current errors."""
        self.errors = self.errors + errors

    def full_error_messages(self):
        """Return all messages from all errors."""
        return [error.message for error in self.errors]

    def check_presence(self, value, name):
        """Check presence of value and set errors if it does not exist."""
        if value:
            return True

        self.add_error(
            code="presence",
            message=f"{name} cannot be blank.",
            details=[{"attribute": str(name), "value": str(value)}],
        )
        return False

    def check_uniqueness(self, values, name):
        """Check the uniqueness of values and set errors if not unique."""
        if len(set(values)) == len(values):
            return True

        self.add_error(
            code="uniqueness",
            message=f"Every {name} must be unique.",
            details=[{"attribute": str(name), "value": str(values)}],
        )
        return False
