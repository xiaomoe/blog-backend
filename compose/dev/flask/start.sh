#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

flask --app start:app run --host 0.0.0.0
