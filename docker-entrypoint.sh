#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

python manage.py migrate --noinput
python manage.py create_superuser || true

exec "$@"
