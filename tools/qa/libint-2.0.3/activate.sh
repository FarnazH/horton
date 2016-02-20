NAMEVER=$(basename $(dirname "${BASH_SOURCE[0]}"))
source tools/qa/common.sh
if [ -d "${CACHED}/${NAMEVER}/lib" ]; then
    echo -e "${GREEN}Activating ${NAMEVER}${RESET}"
    export LD_LIBRARY_PATH=${CACHED}/${NAMEVER}/lib:${LD_LIBRARY_PATH}
    export CPATH=${CACHED}/${NAMEVER}/include/libint2:${CPATH}
fi
