#!/usr/bin/env bash
set -euo pipefail

script_path=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
base_path=$(dirname -- "$script_path")
test_pattern="test*.py"

while [[ $# -gt 0 ]]; do
	case "$1" in
		--unit)
			;;
		--tests)
			if [[ $# -lt 2 ]]; then
				echo "[e] --tests requires a unittest filename pattern." >&2
				exit 2
			fi
			test_pattern="$2"
			shift
			;;
		*)
			echo "[e] Unknown parameter: $1" >&2
			exit 2
			;;
	esac
	shift
done

echo "[v] Running WatchWolf-Client unit tests in Docker..."
docker run --rm --network none \
	--mount "type=bind,source=$base_path,target=/app,readonly" \
	--workdir /app \
	--env PYTHONDONTWRITEBYTECODE=1 \
	python:3.12-slim \
	python3 -m unittest discover --start-directory tests --pattern "$test_pattern" --verbose

echo "[i] Unit tests passed"
