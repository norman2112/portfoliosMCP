#!/bin/bash
#poetry config installer.modern-installation false
poetry env use system
poetry lock --no-update
poetry add debugpy
poetry install --sync --no-interaction|| echo 'can not install the platforma packages, please check the AWS keys in docker-compose'
