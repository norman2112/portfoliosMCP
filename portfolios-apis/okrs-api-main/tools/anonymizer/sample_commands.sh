#!/usr/bin/env bash

# These are a string of sample commands, designed to illustrate the process.
# First we dump the relevant data
pg_dump --clean --schema=public --disable-triggers -t objectives -t key_results -t progress_points -t work_item_containers -t settings postgres://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/postgres > /tmp/production_dump.sql
# Creat the temporary database
createdb pg_copy
# Load the data from the first step into the temporary database.
psql -f /tmp/production_dump.sql pg_copy
# Anonymize the temporary database based on the config in the config.yml file
pganonymize --schema=tools/anonymizer/config.yml --dbname=pg_copy --user=${PGUSER} --password=${PGPASSWORD} --host=${PGHOST} --port=${PGPORT}
# Dump that anonymized database
pg_dump postgres://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/pg_copy > /tmp/anonymous.sql
