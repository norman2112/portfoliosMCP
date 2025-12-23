okrs-api
========

.. image:: https://github.com/pv-platforma/okrs-api/workflows/ci/badge.svg
   :target: https://github.com/pv-platforma/okrs-api/actions?query=workflow%3Aci
.. image:: https://coveralls.io/repos/github/pv-platforma/okrs-api/badge.svg?t=DAHQFk
  :target: https://coveralls.io/github/pv-platforma/okrs-api

The API for the OKRs project

Latest Docs
-----------
The latest docs can be found at https://didactic-tribble-9b4553ff.pages.github.io

Below are the previous docs for OKRs which are likely not kept up to date


Description
-----------

The `openapi/openapi.yml` file in this repository is an
`OpenAPI Specification <https://swagger.io/specification>`_ based file which
represents paths and components for this api.

This file is used to generate api endpoints (paths), models, migrations, data
validation, and controller scaffolding. The migrations can be used to generate
the schema for the database specified for this project.

The respository also contains metadata for a Hasura GraphQL instance based on
the same database schema for this project in `hasura/hasura_metadata.json`.

Quickstart
----------

Start up the docker container::

  docker-compose up

This will start up

- your database (accessible on port 5431)
- your Hasura container (accessible on port 8081)
- the okrs-api app (accessible on port 8000).

General Usage
^^^^^^^^^^^^^

Make sure `Poetry`_ and `Invoke`_ are installed. You will need these
commands if you wish to use the tasks available::

  brew install poetry pyinvoke

Configure the AWS Code artifact access::

  eval $(inv setup.poetry)

.. warning::

  This requires a programmatic access or a valid AWS session token.

Generate the PTS Token
^^^^^^^^^^^^^^^^^^^^^^

The Planview Token Service token is passed into Hasura. If you wish to
generate a new token, you may use the built-in tool to use it.

Example::

  inv generate.pts-jwt -a 'leankit' -u 12345 -o 67899 -e d09 -d d09.leankit.io

The above is a command that gets a PTS token that gives the user access to the
Leankit API. (Your Leankit user id and organization id will be different).

Once you have a valid PTS token, you may add it to your Hasura headers from
the Hasura web console.

Run Via Docker-Compose
^^^^^^^^^^^^^^^^^^^^^^
You can run the entire project via docker-compose by executing the command ::

  docker-compose up --build

Or if nothing has changed related to the build or dependencies, simply run ::

  docker-compose up

Authentication
--------------

Authentication variables are configured in the docker-compose.yml file at the root of the project.

By default, docker compose is set to accept and verify a real token from the development platforma token service ::

  HASURA_GRAPHQL_JWT_SECRET: "{\"type\": \"RS256\", \"jwk_url\": \"https://cognito-idp.us-west-2.amazonaws.com/us-west-2_EgR4jyqiX/.well-known/jwks.json\", \"claims_format\": \"stringified_json\"}"

This option should be used when running dovetail via npm run dev:core.

If you instead wish to use a locally generated token, the environment variable can be switched out with a hardcoded key ::

  HASURA_GRAPHQL_JWT_SECRET: "{\"type\": \"HS256\", \"key\":\"~~dev_hasura_graphql_jwt_secret~~\", \"claims_format\": \"stringified_json\"}"

This option is compatible with the npm run dev:core:local command in dovetail.

Further information about how hasura manages auth can be found `in their documentation <https://hasura.io/docs/latest/graphql/core/auth/authentication/jwt/>`_.

Seed the database
^^^^^^^^^^^^^^^^^

.. code-block:: bash

  poetry run inv setup.seed

Create your Controllers
^^^^^^^^^^^^^^^^^^^^^^^

Controllers should be and placed in the `okrs_api/api/controller` directory.

A task was provided to help with this effort, and will generate the scaffolding
for the discovered endpoints.

.. code-block:: bash

  poetry run inv generate.controllers


Show the Swagger documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To bring up the Swagger documentation for your local instance::

  open http://localhost:8000/api/ui/

More About Migrations
---------------------

If changes are made to the `openapi.yml` file, a new migration that will reflect
those changes can be auto-generated::

  poetry run inv migration.generate

To add a new migration manually, run::

  poetry run inv migration.new

Migrations are generated using the `Alembic`_ tool for `SQLAlchemy`_.

Using `Alembic`_, migrations can be upgraded or downgraded as follow::

  poetry run alembic downgrade base # migrate all the way down
  poetry run alembic downgrade -1 # revert the latest applied version
  poetry run alembic upgrade +1 # migrate up 1 version

For more migration functionality, see the `Alembic`_ documentation.

Timestamp Migrations
^^^^^^^^^^^^^^^^^^^^

Any `date` or `date-time` property in the openapi.yml file, after migrating the
database, will result in a `timestamp` column. To convert this `timestamp`
column to a `timestampz` column (with a time zone), a manual migration wiil have
to be created::

  poetry run inv migration.timestamp

.. _Alembic: https://alembic.sqlalchemy.org/en/latest/
.. _Invoke: https://www.pyinvoke.org
.. _OpenAlchemy extension properties: https://openapi-sqlalchemy.readthedocs.io/en/latest/#how-does-it-work
.. _Poetry: https://python-poetry.org/
.. _SQLAlchemy: https://www.sqlalchemy.org/

Testing
^^^^^^^
If you wish to do testing, then your tests will need access to the database
directly. You must first set your DATABASE_URL in your environment to the
okrs database in docker::

  DATABASE_URL=postgresql://okruser:changeMe@localhost:5431/okrs

You may then run the ci::

  poetry run inv ci

