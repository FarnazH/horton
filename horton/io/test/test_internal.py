# -*- coding: utf-8 -*-
# Horton is a development platform for electronic structure methods.
# Copyright (C) 2011-2013 Toon Verstraelen <Toon.Verstraelen@UGent.be>
#
# This file is part of Horton.
#
# Horton is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# Horton is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
#
#--
#pylint: skip-file


import h5py as h5

from horton import *
from horton.test.common import tmpdir
from horton.io.test.common import compare_data


def test_consistency_file():
    with tmpdir('horton.io.test.test_chk.test_consistency_file') as dn:
        fn_h5 = '%s/foo.h5' % dn
        fn_fchk = context.get_fn('test/water_sto3g_hf_g03.fchk')
        fn_log = context.get_fn('test/water_sto3g_hf_g03.log')
        data1 = load_smart(fn_fchk, fn_log)
        data1['wfn'].clear_dm()
        dump_smart(fn_h5, data1)
        data2 = load_smart(fn_h5)
        compare_data(data1, data2)


def test_consistency_core():
    with h5.File('horton.io.test.test_chk.test_consistency_core', driver='core', backing_store=False) as f:
        fn_fchk = context.get_fn('test/water_sto3g_hf_g03.fchk')
        fn_log = context.get_fn('test/water_sto3g_hf_g03.log')
        data1 = load_smart(fn_fchk, fn_log)
        data1['wfn'].clear_dm()
        dump_smart(f, data1)
        data2 = load_smart(f)
        compare_data(data1, data1)
