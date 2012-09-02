#!/bin/bash
for i in $(find horton tools | egrep "\.pyc$|\.py~$|\.pyc~$|\.bak$|\.so$") ; do rm -v ${i}; done
rm -vr doc/_build/
rm -v MANIFEST
rm -vr dist
rm -vr build
rm -v horton/gbasis/cext.cpp
rm -v horton/atgrid/cext.cpp
