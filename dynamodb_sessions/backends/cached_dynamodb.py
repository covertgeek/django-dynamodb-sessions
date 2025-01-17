"""
Cached, DynamoDB-backed sessions.
"""

from django.conf import settings
from django.core.cache import cache

from dynamodb_sessions.backends.dynamodb import SessionStore as DynamoDBStore

KEY_PREFIX = "dynamodb_sessions.backends.cached_dynamodb"


class SessionStore(DynamoDBStore):
    """
    Implements cached, database backed sessions.
    """

    def __init__(self, session_key=None):
        super().__init__(session_key)

    @property
    def cache_key(self):
        return KEY_PREFIX + self._get_or_create_session_key()

    def load(self):
        data = cache.get(self.cache_key, None)
        if data is None:
            data = super().load()
            if self.session_key is not None:
                cache.set(self.cache_key, data, self.get_expiry_date())
        return data

    def exists(self, session_key):
        if session_key and (KEY_PREFIX + session_key) in cache:
            return True
        return super().exists(session_key)

    def save(self, must_create=False):
        super().save(must_create)
        cache.set(self.cache_key, self._session, self.get_expiry_age())

    def delete(self, session_key=None):
        super().delete(session_key)
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        cache.delete(KEY_PREFIX + session_key)

    def flush(self):
        """
        Removes the current session data from the database and regenerates the
        key.
        """

        self.clear()
        self.delete(self.session_key)
        self._session_key = None
