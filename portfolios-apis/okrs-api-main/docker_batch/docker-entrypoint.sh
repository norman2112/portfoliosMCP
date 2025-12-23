#!/bin/bash
set -eo pipefail
# Ensure we are in the app folder.
cd /usr/src/app

# Print some debugging information.
echo "PARAMS"
echo $*

# Start the batch job.
exec account-migrate $*

