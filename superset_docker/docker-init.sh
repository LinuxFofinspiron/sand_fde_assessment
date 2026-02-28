#!/bin/bash
set -e

# 1. Upgrade the DB to create tables (including the missing 'themes' table)
superset db upgrade

# 2. Create an admin user (using env vars or defaults)
# These env vars can be set in your docker-compose or docker run command
superset fab create-admin \
              --username "${ADMIN_USERNAME:-admin}" \
              --firstname "${ADMIN_FIRSTNAME:-Superset}" \
              --lastname "${ADMIN_LASTNAME:-Admin}" \
              --email "${ADMIN_EMAIL:-admin@fab.org}" \
              --password "${ADMIN_PASSWORD:-admin}"

# 3. Create default roles and permissions
superset init

# 4. Start the server (matching your log's gunicorn config)
gunicorn \
    --bind  0.0.0.0:8088 \
    --workers 1 \
    --timeout 60 \
    --limit-request-line 0 \
    --limit-request-field_size 0 \
    --worker-class gthread \
    "superset.app:create_app()"