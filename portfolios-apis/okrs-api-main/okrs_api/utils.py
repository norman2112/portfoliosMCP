"""General purpose utilities."""

from datetime import datetime, timezone
import json


def minmax(number, minimum=0, maximum=100):
    """Clip a number at minimum and maximum."""
    return max([minimum, min([maximum, number])])


def utc_timestamp():
    """
    Return a UTC timestamp for right now.

    Due to changes in Python 3, this is the preferred way to get a UTC timestamp
    that will not change with timezone. This is suitable for database columns
    that need a timestamp.
    """
    return datetime.now(timezone.utc).isoformat()


def lower_keys(original_dict):
    """Lower all the keys in a dictionary, recursively."""
    new_dict = {}
    for k, v in original_dict.items():
        if isinstance(v, dict):
            v = lower_keys(v)
        new_dict[k.lower()] = v
    return new_dict


class Map(dict):
    """
    A Dot-notation map for data structures.

    This can operate and retrieve data as either a dict or an object.

    Credit here: https://stackoverflow.com/questions/2352181
    """

    def __init__(self, *args, **kwargs):
        """Initialize the map."""
        super().__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        """Use this to get via dot-notation."""
        return self.get(attr)

    def __setattr__(self, key, value):
        """Use this to set via dot-notation."""
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        """Use this to set via key/value dict notation."""
        super().__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        """Use this to delete via dot notation."""
        self.__delitem__(item)

    def __delitem__(self, key):
        """Use this to delete via key dict notation."""
        super().__delitem__(key)
        del self.__dict__[key]


async def apply_inject(source, target_key, transformer_fn):
    """Apply a function on an object and inject the result."""
    if isinstance(source, list):
        for s in source:
            s[target_key] = await transformer_fn(s)
    else:
        source[target_key] = await transformer_fn(source)

    return source


def normalise(url):
    """Remove the starting protocol part from the URL if any."""

    if url.startswith("https"):
        return url[8:]

    if url.startswith("http"):
        return url[7:]

    return url


def get_tenant_id(env_selectors, product_type):
    """Get correct tenant id from env selectors."""

    if product_type == "leankit":
        return env_selectors.get(product_type)

    if product_type == "e1_prm":
        selector = env_selectors.get(product_type)
        if selector.startswith("E1_PRM~") or selector.startswith("e1_prm~"):
            return selector[7:]
        return selector

    return None


def adapt_error_for_hasura(error_obj, code):
    """Convert error from API to Hasura specific format."""
    return (
        dict(
            message=json.dumps(error_obj), extensions=dict(code=code, details=error_obj)
        ),
        code,
    )


def get_valid_action(action_name):
    """Get valid action name."""
    if action_name in ["current_user_async", "basic_current_user"]:
        return "current_user"
    if action_name == "list_activity_containers_async":
        return "list_activity_containers"
    return action_name


def parse_datetime_str(dt_str):
    """Parse datetime string into datetime object in utc."""
    try:
        return datetime.fromisoformat(dt_str).astimezone(timezone.utc)
    except Exception as e:
        raise ValueError(f"Invalid date format: {e}") from e


def append_error(errors, error_code, message):
    """Append error code and message to errors list."""
    errors.append(
        {
            "message": message,
            "error_code": error_code,
        }
    )
