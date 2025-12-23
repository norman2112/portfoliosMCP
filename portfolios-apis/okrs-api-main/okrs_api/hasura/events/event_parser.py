"""Parsers for all Hasura Event-related code."""


class EventParser:
    """Parse the event data posted from Hasura and provide convenience methods."""

    def __init__(self, event_body):
        """
        Initialize with the event data from Hasura.

        :param dict event_body: the event body from Hasura.

        Hasura event_body will look like this::

        {
            "event": {
                "session_variables": <session-variables>,
                "op": "<op-name>",
                "data": {
                    "old": <column-values>,
                    "new": <column-values>
                }
            },
            "created_at": "<timestamp>",
            "id": "<uuid>",
            "trigger": {
                "name": "<name-of-trigger>"
            },
            "table":  {
                "schema": "<schema-name>",
                "name": "<table-name>"
            }
        }

        More info here: https://hasura.io/docs/1.0/graphql/core/event-triggers
        """
        self.event_body = event_body

    def trigger_name(self):
        """Return the event trigger name."""
        return self.event_body.get("trigger", {})["name"]

    @property
    def table(self):
        """Event table in Hasura."""
        return self.event_body.get("table", {}).get("name")

    @property
    def detail(self):
        """Event detail from Hasura."""
        return self.event_body.get("event", {})

    @property
    def created_at(self):
        """Event created_at from Hasura."""
        return self.event_body.get("created_at")

    @property
    def event_id(self):
        """Event id from Hasura."""
        return self.event_body.get("id")

    @property
    def data(self):
        """Get 'data' from the event detail."""
        return self.detail.get("data", {})

    @property
    def new_data(self):
        """
        Get 'new' key from data.

        Since the value may be explicitly set to None upstream, we
        explicitly set the value to an empty dict if that is the case.
        """
        return self.data.get("new") or {}

    @property
    def old_data(self):
        """
        Get 'old' key from data.

        Since the value may be explicitly set to None upstream, we
        explicitly set the value to an empty dict if that is the case.
        """
        return self.data.get("old") or {}

    def find_value_for_key(self, key):
        """Return a value for a key in either new or old data."""
        return self._combined_data.get(key)

    def subset_data(self, keys):
        """Return a new dict of the subset of the keys requested."""
        return {key: self._combined_data.get(key) for key in keys}

    @property
    def tenant_id_str(self):
        """
        Return the tenant_id_str, if it exists.

        This is a convenience method for a common attribute.
        """
        return self.find_value_for_key("tenant_id_str")

    @property
    def tenant_group_id_str(self):
        """
        Return the tenant_group_id_str, if it exists.

        This is a convenience method for a common attribute.
        """
        return self.find_value_for_key("tenant_group_id_str")

    @property
    def _combined_data(self):
        """
        Return the merged data of new data and old data.

        The combined data will be the old data overwritten [when necessary] by
        the new data.
        """
        return (self.old_data or {}) | (self.new_data or {})

    @property
    def operation(self):
        """
        Get operation event detail.

        For "MANUAL" ops, we can assume that the operation is an INSERT,
        as MANUAL means that the event was triggered directly from the
        Hasura console.
        https://hasura.io/docs/latest/graphql/core/event-triggers/invoke-trigger-manually.html

        For "UPDATE" ops where the attributes have a non-null value for the
        `deleted_at` attribute, we return "delete". This will make the rest
        of the app operate as if the record had been deleted.
        """
        op = self.detail.get("op").lower()
        if op == "manual":
            return "insert"

        if op == "update" and self.is_soft_delete():
            return "delete"

        return op

    @property
    def event_is_deletion(self):
        """Return True if the operation is of type 'delete'."""
        return self.operation == "delete"

    @property
    def event_is_insertion(self):
        """Return True if the operation is of type 'insert'."""
        return self.operation == "insert"

    @property
    def event_is_update(self):
        """Return True if the operation is of type 'update'."""
        return self.operation == "update"

    @property
    def changed_attribs(self):
        """Return the attributes that have changed."""
        if not self.event_is_update:
            return self._combined_data

        return {k: v for (k, v) in self.new_data.items() if v != self.old_data[k]}

    def in_changed_keys(self, keys):
        """
        Return a bool if any of the keys passed in have been changed.

        If any of the data represented by the keys that are passed in has been
        changed, return True.

        :param list keys: the list of keys to check against
        """
        changed_keys = self.changed_attribs.keys()
        return bool(set(keys) & set(changed_keys))

    def is_soft_delete(self):
        """Determine if this is a soft delete."""
        if bool(self._combined_data.get("deleted_at_epoch")):
            return True
        return bool(self._combined_data.get("is_deleted"))

    def writeback(self, changes):
        """
        Write back changes that have been made to the event data.

        This is useful for when the event parser is passed along to another
        event handler that will need to know about the event changes. The
        changes are always written back to the `new` key in the data,
        regardless of operation.

        :param dict changes: a dict of changes to update

        returns the new data after updates.
        """
        self.event_body["event"]["data"]["new"] = self.new_data | changes
        return self.new_data
