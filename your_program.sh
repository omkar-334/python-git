#!/bin/sh
set -e
PYTHONPATH=$(dirname $0) exec python3 -m app.main "$@"
