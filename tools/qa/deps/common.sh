# This file gets sourced by all install and activate scripts

# Some colors
GREEN='\e[0;32m'
RED='\e[0;31m'
RESET='\e[0m'

# Make sure there is a ${QAWORKDIR}
[[ -z ${QAWORKDIR} ]] && export QAWORKDIR=${PWD}/qaworkdir
[[ -d ${QAWORKDIR} ]] || mkdir -p ${QAWORKDIR}
