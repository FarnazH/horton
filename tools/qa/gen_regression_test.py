#!/usr/bin/env python
# -*- coding: utf-8 -*-
# HORTON: Helpful Open-source Research TOol for N-fermion systems.
# Copyright (C) 2011-2016 The HORTON Development Team
#
# This file is part of HORTON.
#
# HORTON is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# HORTON is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --
"""Script to generate regression tests.

To use, simply pass the name of the example python script.  It will write a testing script in your
current directory with name test_<orig_script_name>.py, which can be used with nosetests.

There are several limitations.
1) All of the variable types to be checked must by numpy compatible. You cannot specify a class.
For things like integrals, access the _array attribute if necessary.
2) The original script must have variables named starting with "result_". These will be
checked.
3) If the variables to be checked need tolerances, they must be named starting with
"threshold_" and the name must match the corresponding "result_" variable.
4) The original example script cannot be moved, or the regression tests must be regenerated.
5) The variables get printed into the unit test. Try to avoid dumping large things like
two-electron integrals.
"""
import sys
import numpy as np


def gen_regression_test():
    # Set global configurations
    np.set_printoptions(threshold=np.inf)

    # Set defaults for path
    default_threshold = 1e-8

    # Set path to operate on
    test_path = sys.argv[1]

    # Generate reference values
    with open(test_path) as fh:
        exec fh

    # If the example has no result_ variables, then skip the file and just return
    if not any(["result_" in k for k in locals()]):
        return None

    # Scan for variables starting with result_ and threshold_
    results = []
    thresholds = {}

    # unit_test is the contents of the unit_testing script. Whitespace matters!
    # first generate the header
    unit_test = """# -*- coding: utf-8 -*-
# HORTON: Helpful Open-source Research TOol for N-fermion systems.
# Copyright (C) 2011-2016 The HORTON Development Team
#
# This file is part of HORTON.
#
# HORTON is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# HORTON is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
# --

from numpy import array, allclose
from nose.plugins.attrib import attr\n"""

    # Generate the function name.
    test_name = test_path.split("/")[-1].split(".py")[0]
    unit_test += """

@attr('regression_check')
def test_{0}():\n""".format(test_name)

    # first set all tolerances to default
    for k, v in locals().items():
        if k.startswith("result_"):
            assert isinstance(v, (int, float, np.ndarray))
            unit_test += "    ref_{name} = {value}\n".format(name=k, value=v.__repr__())
            results.append("ref_{0}".format(k))
            thresholds["ref_{0}".format(k)] = default_threshold

    # afterwards overwrite tolerances with user-specified ones
    for k, v in locals().items():
        if k.startswith("threshold_"):
            assert isinstance(v, (int, float))
            var_name = k.split("threshold_")[-1]
            thresholds["ref_result_{0}".format(var_name)] = v

    for k in thresholds:
        assert k in results

    unit_test += """
    results = {r}
    thresholds = {t}
""".format(r=results, t=thresholds)

    # Execute script in unit test
    unit_test += """
    with open("{0}") as fh:
        exec fh
""".format(test_path)

    # Compare results with references. Must be a numpy compatible type.
    unit_test += """
    l = locals()
    for r in results:
        var_name = r.split("ref_")[-1]
        assert allclose(l[var_name], l[r], thresholds[r])"""

    with open("test_{0}".format(test_path.split("/")[-1]), "w") as fh:
        fh.write(unit_test)

    print "\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "== SUCCESSFULLY GENERATED TEST SCRIPT =="
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"

if __name__ == "__main__":
    gen_regression_test()
