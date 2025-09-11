#!/bin/bash

# to stop the script if a command fail
set -e

# Folder where the makefile is located
MAKE_TEST="$(pwd)/legacy/ocaml-old-project"

# Script Python à exécuter
PYTHON_TEST="python -m pytest python-geneweb-modernization/unit_tests/ -v"

# Sauvegarde du répertoire courant
CURRENT_DIR=$(pwd)

echo "================================== Test execution of the old project =================================="
cd "$MAKE_TEST"
eval $(opam env)
ocaml ./configure.ml
make build-geneweb
make test
echo "================================== End of the test execution of the old project =================================="

cd "$CURRENT_DIR"

echo "================================== Test execution of the new project =================================="

${PYTHON_TEST}

echo "================================== End of the test execution of the new project =================================="

cd "$CURRENT_DIR"

echo "=== Script terminé avec succès ==="
