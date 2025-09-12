#!/bin/bash

# to stop the script if a command fail
# set -e

# Folder where the makefile is located
MAKE_TEST="$(pwd)/legacy/ocaml-old-project"

# Script Python à exécuter
PYTHON_TEST_SPECIFIC_TEST_WITH_PYTEST="python -m pytest tests/backend_tests -v"

# Sauvegarde du répertoire courant
CURRENT_DIR=$(pwd)

echo "================================== Test execution of the old project ============================================="
cd "$MAKE_TEST"
eval $(opam env)
ocaml ./configure.ml
make build-geneweb

echo "⏱ Attente de 3 secondes avant de lancer make test..."
sleep 3

make test
echo "================================== End of the test execution of the old project =================================="

make clean

cd "$CURRENT_DIR"

echo "================================== Test execution of the new project ============================================="

${PYTHON_TEST_SPECIFIC_TEST_WITH_PYTEST}

cd "$CURRENT_DIR"

python -m unittest -v tests/backend_tests/test_basic.py

python tests/backend_tests/test_compliance.py

python tests/backend_tests/test_server.py



echo "================================== End of the test execution of the new project =================================="
