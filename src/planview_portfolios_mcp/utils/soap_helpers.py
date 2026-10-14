"""Shared SOAP utilities for field normalization."""

from typing import Any


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase.

    Args:
        snake_str: String in snake_case or already PascalCase

    Returns:
        String in PascalCase

    Examples:
        >>> to_pascal_case("father_key")
        'FatherKey'
        >>> to_pascal_case("FatherKey")
        'FatherKey'
    """
    # If already PascalCase (first char is uppercase), return as-is
    if snake_str and snake_str[0].isupper():
        return snake_str
    # Convert snake_case to PascalCase
    return "".join(word.capitalize() for word in snake_str.split("_"))


def filter_and_sort_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Filter None values, convert to PascalCase, and sort alphabetically.

    Args:
        data: Dictionary with potential None values and snake_case or PascalCase keys

    Returns:
        Filtered and sorted dictionary with PascalCase keys

    Notes:
        - Planview SOAP API requires fields in alphabetical order
        - Field names must be PascalCase (e.g., FatherKey, not father_key)
        - None values are automatically filtered (zeep drops them anyway)
        - This pattern is used across all SOAP operations

    Examples:
        >>> filter_and_sort_fields({"father_key": "key://2/$Plan/123", "description": "Task", "notes": None})
        {'Description': 'Task', 'FatherKey': 'key://2/$Plan/123'}
    """
    # Convert keys to PascalCase and filter None values
    pascal_dict = {to_pascal_case(k): v for k, v in data.items() if v is not None}
    # Sort alphabetically
    return dict(sorted(pascal_dict.items()))
