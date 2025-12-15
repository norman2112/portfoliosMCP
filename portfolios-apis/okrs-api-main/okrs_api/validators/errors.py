"""Module for all validation error related code."""
import json


class ValidationError:
    """The validations error class."""

    def __init__(self, code, message, details=None):
        """
        Initialize the error.

        :param str code: the error code
        :param str message: the error message
        :param [dict] details: the error details for interpolation
        """
        self.code = code
        self.message = message
        self._details = details or []

    @property
    def details(self):
        """Stringify all values of the dicts in the details."""
        return [self._stringify_values(detail) for detail in self._details]

    def to_dict(self):
        """Return a serializable dict representation of the error."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def _stringify_values(self, detail):
        stringified_dict = {}
        for key in detail:
            if isinstance(detail[key], dict):
                stringified_dict[key] = json.dumps(detail[key])
            else:
                stringified_dict[key] = str(detail[key])
        return stringified_dict
