# ########################################################################
# platforma base image as builder
# platforma base image is maintained by platforma devops
# ########################################################################
FROM 486329218230.dkr.ecr.us-west-2.amazonaws.com/os/python:3.9.2-slim-buster as builder
LABEL maintainer="okrs-api"

# switch to root user to install additional dependencies
USER root

# app specific dir
WORKDIR /usr/src/app

# Copy the codebase
COPY . .

RUN poetry build -f wheel \
  && poetry export --without-hashes > requirements.txt \
  && pip wheel -w /usr/src/app/deps/ -r requirements.txt \
  && cp dist/* /usr/src/app/deps/

# #########################################
# Runtime Container
# #########################################
FROM 486329218230.dkr.ecr.us-west-2.amazonaws.com/os/python:3.9.2-slim-buster  as runtime
LABEL maintainer="okrs-api"

# switch to root user to install additional dependencies
USER root

# Copy the all required folders to the location /usr/src/app
COPY openapi /usr/src/app/openapi
COPY alembic /usr/src/app/alembic
COPY hasura /usr/src/app/hasura
COPY hasura-reporting /usr/src/app/hasura-reporting

# Copy the all required files to the location /usr/src/app
COPY docker/docker-entrypoint.sh alembic.ini tasks.py pyproject.toml poetry.lock poetry_setup.sh /usr/src/app/

# setting required priviledges for platforma on the directory
RUN chown -R platforma:platforma /usr/src/app

# copy the dependencies installed from builder
COPY --from=builder /usr/src/app/deps/ /usr/src/tmp/

RUN pip install --no-cache-dir /usr/src/tmp/* \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/src/tmp/* \

USER platforma
WORKDIR /opt/app

# Set entrypoint.
ENTRYPOINT ["/usr/src/app/docker-entrypoint.sh"]