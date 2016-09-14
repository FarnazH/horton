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

from numpy import array, allclose
from nose.plugins.attrib import attr

from horton import context


@attr('regression_check')
def test_rhf_water_dense():
    ref_result_energy = -75.585812494951796
    ref_result_exp_alpha = array([[ -2.38144405e-03,   1.16404016e-01,   2.33907104e-01,
         -1.25637426e-01,   3.55124631e-17,  -5.31255186e-02,
          3.01170958e-02,  -9.73645171e-01,  -9.78686530e-01,
          7.18921252e-16,   2.22071217e-01,   1.70460984e-01,
         -2.58083716e-01],
       [ -6.97960952e-03,   1.99295419e-02,   1.78029192e-01,
         -1.03999576e-01,   1.87232664e-16,  -8.66086351e-01,
          1.16421959e+00,   6.62087503e-01,   4.93573632e-01,
          6.55982557e-16,   9.90390386e-02,   4.93752831e-01,
         -3.66057651e-01],
       [ -9.83218668e-01,  -2.29780750e-01,   5.98206912e-16,
         -8.47067333e-02,   2.48045950e-16,  -1.11458552e-01,
          3.81544322e-15,  -5.03087015e-15,  -6.67068760e-02,
          1.47074238e-16,   4.03282090e-02,  -2.52494163e-16,
          8.68394173e-02],
       [ -9.58359077e-02,   2.18009353e-01,  -4.27577532e-16,
          7.87967541e-02,  -7.42532435e-17,   3.63081545e-02,
         -2.24664108e-15,   3.80822859e-15,   8.88316282e-02,
         -5.00249610e-16,  -1.16609145e-01,  -1.32734938e-15,
         -1.64079143e+00],
       [  3.81971424e-17,  -1.52470836e-15,   3.96354006e-01,
          4.24499546e-15,   5.84832396e-17,  -8.33854189e-15,
         -3.01648973e-01,   2.05394540e-01,  -1.60836181e-14,
          7.87396237e-16,  -4.35462516e-15,   1.06649468e+00,
         -8.62622624e-16],
       [  3.39664672e-03,  -7.91603839e-02,  -4.26054210e-15,
          4.47104804e-01,  -9.97846461e-17,  -2.03067932e-01,
          5.66907243e-15,  -2.03834959e-14,  -2.40544838e-01,
         -3.44448293e-15,  -1.01845647e+00,  -4.15219362e-15,
          1.46879875e-01],
       [ -3.55973968e-17,  -1.04759867e-18,   9.74116590e-17,
          2.12252850e-16,   5.20489521e-01,  -1.31655233e-16,
         -1.17966831e-16,  -2.92715480e-16,   4.36788600e-16,
         -1.02967845e+00,   3.32837278e-15,   8.70018665e-16,
          1.31601153e-16],
       [  3.78634203e-02,   7.08505703e-01,  -3.83922304e-15,
          3.89695733e-01,  -4.34255696e-16,   1.05541448e+00,
         -3.25296331e-14,   1.06875668e-14,   1.12159865e-01,
         -4.81839865e-16,  -1.67775496e-01,   6.22576709e-16,
          1.97834381e+00],
       [ -5.39643611e-18,  -2.42240021e-16,   3.67308615e-01,
          3.83746568e-15,   7.32297586e-17,  -2.44062817e-14,
         -7.81482892e-01,   4.63331987e-01,  -3.60721774e-14,
         -1.15991242e-15,   5.66026187e-15,  -1.43027915e+00,
          2.68622597e-16],
       [ -6.31190927e-03,  -8.86898998e-02,  -4.46324170e-15,
          5.19382184e-01,  -9.23056631e-17,  -4.49561847e-01,
          1.35436300e-14,  -2.37375654e-14,  -2.97425968e-01,
          3.60680737e-15,   1.12454691e+00,   4.59904013e-15,
         -4.48340666e-01],
       [  1.33258801e-16,   7.51467326e-18,   4.90552515e-17,
          2.93265239e-16,   6.32856855e-01,   3.03158878e-16,
          1.56968815e-17,   1.78418582e-16,  -3.73763114e-16,
          9.64696458e-01,  -3.23444823e-15,  -6.74301955e-16,
         -6.11144215e-17],
       [ -2.38144405e-03,   1.16404016e-01,  -2.33907104e-01,
         -1.25637426e-01,   3.14366209e-16,  -5.31255186e-02,
         -3.01170958e-02,   9.73645171e-01,  -9.78686530e-01,
         -1.99754288e-16,   2.22071217e-01,  -1.70460984e-01,
         -2.58083716e-01],
       [ -6.97960952e-03,   1.99295419e-02,  -1.78029192e-01,
         -1.03999576e-01,   2.00974672e-16,  -8.66086351e-01,
         -1.16421959e+00,  -6.62087503e-01,   4.93573632e-01,
          6.50375670e-16,   9.90390386e-02,  -4.93752831e-01,
         -3.66057651e-01]])

    results = ['ref_result_energy', 'ref_result_exp_alpha']
    thresholds = {'ref_result_exp_alpha': 1e-08, 'ref_result_energy': 1e-08}

    test_path = context.get_fn("examples/hf_dft/rhf_water_dense.py")
    with open(test_path) as fh:
        exec fh

    l = locals()
    for r in results:
        var_name = r.split("ref_")[-1]
        assert allclose(l[var_name], l[r], thresholds[r]), l[r] - l[var_name]