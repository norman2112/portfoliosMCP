"""Setup for the database."""
from contextlib import contextmanager

import sqlalchemy
from sqlalchemy import orm


async def init(app):
    """Initialize the database connection."""
    # Retrieve the database settings.
    db_settings = app["settings"].database

    # Configure the database engine and session.
    db_settings_dict = db_settings.engine.dict()
    db_url = db_settings_dict.pop("name_or_url")
    db = sqlalchemy.create_engine(db_url, **db_settings_dict)
    db_session = orm.scoped_session(orm.sessionmaker(bind=db))

    # Retrieve the application.
    # Connexion adds a default subapp.
    sub_app = app._subapps[0]

    # Store the information in the application context.
    sub_app["db"] = db
    sub_app["db_session"] = db_session
    yield

    # Disconnect from the database engine on quit().
    try:
        sub_app["db"].dispose()
    except AttributeError as e:
        print(f"cannot close the database connexion: {e}")


@contextmanager
def triggers_disabled_session(engine):
    """
    Return a new session on a new database connection.

    The new database connection will be set to replicate, which disables the
    triggers and allows us to insert with impunity.
    """
    with engine.connect() as connection:
        connection.execute("SET session_replication_role = replica;")
        db_session = sqlalchemy.orm.scoped_session(
            sqlalchemy.orm.sessionmaker(bind=connection)
        )
        yield db_session

    connection.close()
