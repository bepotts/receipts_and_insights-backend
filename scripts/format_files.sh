#!/bin/sh
# Format specific Python files with black and isort

if [ $# -eq 0 ]; then
    echo "No files provided to format"
    exit 1
fi

# Run black and isort on the provided files
black "$@"
isort "$@"

