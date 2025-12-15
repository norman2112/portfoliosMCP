Tools
-----

connexion-controllers
^^^^^^^^^^^^^^^^^^^^^

Generates default connexion controllers from an OpenAPI specification.

Usage
"""""

Generate the controllers::

  poetry run inv generate.controllers --openapi pet_store.yml --output my/api/controller


seeder
^^^^^^

Seeds the database::

  poetry run inv setup.seed
