NAMEVER=$(basename $(dirname "${BASH_SOURCE[0]}"))
source tools/qa/common.sh
if [ -d "${QAWORKDIR}/cached/${NAMEVER}/lib" ]; then
    echo -e "${GREEN}Activating ${NAMEVER}${RESET}"
    export LD_LIBRARY_PATH=${QAWORKDIR}/cached/${NAMEVER}/lib:${LD_LIBRARY_PATH}
    export CPATH=${QAWORKDIR}/cached/${NAMEVER}/include/libint2:${CPATH}
fi
