Usage
-----

Documentation
^^^^^^^^^^^^^

Build the project documentation::

  poetry run inv docs
  open docs/build/html/index.html

View the OpenAPI documentation::

  open http://localhost:8000/api/ui/#/

Test the API
^^^^^^^^^^^^

As the API was generated from an OpenAPI specification, it can be tested
automatically, all without having to write any tests.

This is done by using `Schemathesis`_, a tool leveraging the power of
`Hypothesis`_ to perform property-based testing against the specification.

Run tests::

  poetry run inv test.specification

By default it runs all the checks, but the `--checks` flag can be used to
specified the checks to be performed::

  poetry run inv test.specification --checks=response_schema_conformance

If examples were added to the specification, they will also be injected as input
into the generated test suites.

Other tasks
^^^^^^^^^^^

The available administration tasks can be found by running::

  poetry run inv --list

CORS settings
^^^^^^^^^^^^^

The application comes with default CORS settings. It is recommended to adjust
them to match the application needs.

The setting are located in the
`okrs-api/okrs_api/connexion_utils.py`
file, more specifically, in the `create_connexion_app()` function.

.. _Schemathesis: https://github.com/kiwicom/schemathesis
.. _Hypothesis: https://hypothesis.works/


Health check
^^^^^^^^^^^^

To see if the API is up and running::

  open http://localhost:8000/healthcheck

