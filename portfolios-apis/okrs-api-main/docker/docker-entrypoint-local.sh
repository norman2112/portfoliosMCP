#!/bin/bash
set -eo pipefail
# Ensure we are in the /usr/src/app folder.
cd /usr/src/app

# Print some debugging information.
echo "=============== START DEBUG ==============="
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
cd -

# Start the API.
exec gunicorn \
     --reload \
     --timeout 1800 \
     --log-level debug \
     -b 0.0.0.0:8000 \
     --worker-class aiohttp.GunicornUVLoopWebWorker \
     --access-logfile '-' \
     --access-logformat '%a %t "%r" %s %b %Tf "%{Referer}i" "%{User-Agent}i"' \
     okrs_api.main
