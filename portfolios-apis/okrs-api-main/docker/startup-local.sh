#!/bin/bash
set -eo pipefail

# Print some debugging information.
echo "=============== START DEBUG ==============="
echo "=> Print environment variables"
printenv | sort
echo
echo "=> Printing directory content"
ls -lha
echo "================ END DEBUG ================"
# Run database migrations.
alembic upgrade head

# Import hasura metadata.
echo "--- APPLYING HASURA METADATA ---"
echo "---------------------------------"
cd hasura
hasura metadata apply
cd ..

if [[ -z "$HASURA_DATASERVICE_ENDPOINT" ]]; then
  echo "No data service Hasura found, not applying metadata"
else
  cd hasura-reporting/reporting-metadata
  hasura metadata apply --admin-secret $HASURA_DATASERVICE_ADMIN_SECRET --endpoint $HASURA_DATASERVICE_ENDPOINT
  echo "Data service metadata applied"
  cd ../..
fi

# Start the API.
exec gunicorn \
     --reload \
     --timeout 1800 \
     --log-level debug \
     -b 0.0.0.0:8000 \
     --worker-class aiohttp.GunicornUVLoopWebWorker \
     --access-logfile '-' \
     --access-logformat '%a %t "%r" %s %b %Tf %D "%{Referer}i" "%{User-Agent}i"' \
     okrs_api.main
