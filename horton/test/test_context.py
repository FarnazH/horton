# -*- coding: utf-8 -*-
# Horton is a Density Functional Theory program.
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


import os, subprocess

from horton import context


def test_context():
    fn = context.get_fn('basis/sto-3g.nwchem')
    assert os.path.isfile(fn)
    fns = context.glob('basis/*.nwchem')
    assert fn in fns

def test_data_test_files():
    # Find files in data/test that were not checked in.
    # This test only makes sense if ran inside the source tree.
    if context.data_dir == './data':
        assert os.system('[ -z $(git ls-files --others data/test) ]') == 0, 'Some test files are not staged for commit!'
