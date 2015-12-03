#!/usr/bin/env bash

source tools/qa/deps/common.sh
export NUM_FAILED=0

report_error() {
    echo -e "${RED}${1}${RESET}"
    ((NUM_FAILED++))
}


### Testing in the current branch

### a) Parts that are always done

# Check the author names
./tools/qa/check_names.py || report_error "Failed author/committer check (current branch)"
# Activate dependencies
for DEPDIR in $(cat tools/qa/deps/dirs.txt); do
    [[ -f "tools/qa/deps/${DEPDIR}/activate.sh" ]] && source tools/qa/deps/${DEPDIR}/activate.sh
done
# Clean stuff
./cleanfiles.sh &> /dev/null
rm -rf data/refatoms/*.h5
# Construct the reference atoms
(cd data/refatoms; make all) || report_error "Failed to make reference atoms (current branch)"
# In-place build of HORTON
python setup.py build_ext -i -L ${LD_LIBRARY_PATH} || report_error "Failed to build HORTON (current branch)"
# Run the slow tests
nosetests -v -a slow || report_error "Some slow tests failed (current branch)"
# Build the documentation
(cd doc; make html) || report_error "Failed to build documentation (current branch)"

### b) Parts that depend on the current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "${CURRENT_BRANCH}" != 'master' ]; then
    # Run the first part of the comparative tests if the current branch is not the
    # master branch.
    ./tools/qa/trapdoor_coverage.py feature || report_error "Trapdoor coverage failed (feature branch)"
    ./tools/qa/trapdoor_cppcheck.py feature || report_error "Trapdoor cppcheck failed (feature branch)"
    ./tools/qa/trapdoor_pylint.py feature || report_error "Trapdoor pylint failed (feature branch)"
    ./tools/qa/trapdoor_pep8.py feature || report_error "Trapdoor pep8 failed (feature branch)"
else
    # Run the fast tests
    nosetests -v -a '!slow' || report_error "Some fast tests failed (master branch)"
fi

# Conclude
if [ "$NUM_FAILED" -gt 0 ]; then
    echo -e "${RED}SOME TESTS FAILED (current branch)${RESET}"
    exit 1
fi
echo -e "${GREEN}ALL TESTS PASSED (current branch)${RESET}"
exit 0
