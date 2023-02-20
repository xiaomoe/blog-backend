#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

# db 是 compose 中服务名称
while !</dev/tcp/db/3306; do
    echo "waiting database 1s"
    sleep 1
done
echo "database OK"

exec "$@"
