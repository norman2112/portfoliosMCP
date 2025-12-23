Contributing
============

Instructions for contributors
-----------------------------

We are interested in various different kinds of improvement for okrs-api.
Please feel free to raise an `Issue`_ if you would like to work on something major to
ensure efficient collaboration and avoid duplicate effort.

Guidelines
^^^^^^^^^^

* Use the provided templates to file an `Issue`_ or a `Pull Request`_.

* Create a topic branch from where you want to base your work.

* We follow the `Open Stack Coding Guidelines`_.

* For formatting the files properly, please use `black`_. In the root directory of the
  project, run the following command: `poetry run inv format --write`.

* Make sure you added tests to validate your changes.

* Run all the tests to ensure nothing else was accidentally broken.

* Commit messages must start with a capitalized and short summary (max. 50 chars)
  written in the imperative, followed by an optional, more detailed explanatory text
  which is separated from the summary by an empty line.

* Commit messages should follow best practices, including explaining the context of the
  problem and how it was solved, including in caveats or follow up changes required.
  They should tell the story of the change and provide readers understanding of what led
  to it. Please refer to `How to Write a Git Commit Message`_ for more details.

* If your `Pull Request`_ is a work in progress, create it as a `Draft Pull Request`_.

* Any `Pull Request`_ inactive for 28 days will be automatically closed. If you need
  more time to work on it, ask maintainers, to add the appropriate label to it. Use the
  `@pv-platforma/platforma` mention in the comments.

* Unless explicitly asked, `Pull Request`_ which don't pass all the CI checks will not
  be reviewed. Use the `@pv-platforma/platforma` mention in the comments to ask
  maintainers to help you.

Commit example
""""""""""""""

.. code-block:: bash

  Use Docker Hub build environment values

  Uses the Docker Hub build environment values in order to ensure the
  correct version of okrs-api is installed into the image.

  Fixes pv-platforma/okrs-api#54

The following commit is a good example as:

1. The fist line is a short description and starts with an imperative verb
2. The first paragraph describes why this commit may be useful
3. The last line points to an existing issue and will automatically close it.

Developer setup
---------------

You will need `Python 3` and `poetry`_::

  brew install poetry python@3.8

Fork the project, clone the repository.

Setup a local dev environment::

  poetry install

Run the CI tasks locally ::

  poetry run inv ci

Use `poetry run inv --list` to see all the available tasks. The tasks are created using
`invoke`_.


.. _`Draft Pull Request`: https://github.blog/2019-02-14-introducing-draft-pull-requests/
.. _`How to Write a Git Commit Message`: http://chris.beams.io/posts/git-commit
.. _`Issue`: https://github.com/pv-platforma/okrs-api/issues
.. _`Open Stack Coding Guidelines`: https://docs.openstack.org/charm-guide/latest/coding-guidelines.html
.. _`Pull Request`: https://github.com/pv-platforma/okrs-api/pulls
.. _`black`: https://github.com/psf/black
.. _`invoke`: https://docs.pyinvoke.org/
.. _`poetry`: https://python-poetry.org/
