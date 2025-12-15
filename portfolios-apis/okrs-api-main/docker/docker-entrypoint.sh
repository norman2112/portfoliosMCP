#!/bin/bash
set -eo pipefail
# Ensure we are in the app folder.
cd /usr/src/app

# Print some debugging information.
echo "=============== START DEBUG ==============="
echo "=> Printing directory content"
ls -lha
echo "================ END DEBUG ================"

echo "================ RUNNING DATABASE MIGRATIONS ================"
# Run database migrations.
alembic upgrade head

echo "================ RUNNING HASURA METADATA IMPORT ================"

# Import hasura metadata.
cd hasura
hasura metadata apply
cd -

echo "================ RUNNING HASURA METADATA IMPORT FOR REPORTING ================"

# Import hasura metadata to data service Hasura
if [[ -z "$HASURA_DATASERVICE_ENDPOINT" ]]; then
  echo "No data service Hasura found, not applying metadata"
else
  cd hasura-reporting/reporting-metadata
  hasura metadata apply --admin-secret $HASURA_DATASERVICE_ADMIN_SECRET --endpoint $HASURA_DATASERVICE_ENDPOINT
  echo "Data service metadata applied"
fi
cd -

# Start the API.
echo "=============== STARTING API SERVER ==============="
exec okrs-api
