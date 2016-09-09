#!/usr/bin/env bash

if [ "$BUILDKITE_PULL_REQUEST" != "false" ]; then
    source tools/qa/buildkite_common.sh
    checkout_merge_commit
    get_ancestor  # Writes $ANCESTOR_SHA variable.

    echo "--- Build refatoms"
    rm -rf data/refatoms/*.h5 data/refatoms/*.tar.bz2
    make -C data/refatoms/

    echo "--- Running trapdoors tests"
    ./tools/qa/check_whitespace.py || report_error "Whitespace errors in some commits"

    export PYTHONPATH=`pwd`
    export HORTONDATA=`pwd`/data

    tools/qa/simulate_trapdoor_pr.py -vrA $ANCESTOR_SHA tools/qa/trapdoor_coverage.py -- --nproc=6
    tools/qa/simulate_trapdoor_pr.py -vrA $ANCESTOR_SHA tools/qa/trapdoor_namespace.py
fi
