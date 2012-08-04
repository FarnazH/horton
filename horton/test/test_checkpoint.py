# -*- coding: utf-8 -*-
# Horton is a Density Functional Theory program.
# Copyright (C) 2011-2012 Toon Verstraelen <Toon.Verstraelen@UGent.be>
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


import tempfile, os, h5py as h5

from horton import *


def compare_systems(sys1, sys2):
    assert (sys1.numbers == sys2.numbers).all()
    assert (sys1.coordinates == sys2.coordinates).all()


def test_chk_initialization_filename():
    tmpdir = tempfile.mkdtemp('horton.test.test_checkpoint.test_chk_initialization_filename')
    try:
        fn_chk = '%s/chk.h5' % tmpdir
        sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=fn_chk)
        del sys1
        sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'))
        sys2 = System.from_file(fn_chk)
        compare_systems(sys1, sys2)
    finally:
        if os.path.isfile(fn_chk):
            os.remove(fn_chk)
        os.rmdir(tmpdir)


def test_chk_initialization_file():
    chk = h5.File('horton.test.test_checkpoint.test_chk_initialization_file', driver='core', backing_store=False)
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=chk)
    del sys1
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'))
    sys2 = System.from_file(chk)
    compare_systems(sys1, sys2)
    chk.close()


def test_chk_initialization_override():
    tmpdir = tempfile.mkdtemp('horton.test.test_checkpoint.test_chk_override')
    try:
        fn_chk1 = '%s/chk1.h5' % tmpdir
        fn_chk2 = '%s/chk2.h5' % tmpdir
        sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=fn_chk1)
        del sys1
        sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'))
        sys2 = System.from_file(fn_chk1, chk=fn_chk2)

        compare_systems(sys1, sys2)
        assert os.path.isfile(fn_chk2)

        sys3 = System.from_file(fn_chk2, chk=None)
        compare_systems(sys1, sys3)
        sys3.numbers[:] = 0
        sys3.update_chk('numbers')

        sys4 = System.from_file(fn_chk2, chk=None)
        compare_systems(sys1, sys4)
    finally:
        if os.path.isfile(fn_chk1):
            os.remove(fn_chk1)
        if os.path.isfile(fn_chk2):
            os.remove(fn_chk2)
        os.rmdir(tmpdir)


def test_chk_update1():
    chk = h5.File('horton.test.test_checkpoint.test_chk_update1', driver='core', backing_store=False)
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=chk)
    sys1.numbers[:] = [3, 2]
    sys1.coordinates[0,2] = 0.25
    sys1.update_chk()
    del sys1
    sys1 = System.from_file(chk)
    assert (sys1.numbers == [3, 2]).all()
    assert sys1.coordinates[0,2] == 0.25
    chk.close()


def test_chk_update2():
    chk = h5.File('horton.test.test_checkpoint.test_chk_update2', driver='core', backing_store=False)
    sys1 = System.from_file(context.get_fn('test/hf_sto3g.fchk'), chk=chk)
    sys1.numbers[:] = [3, 2]
    sys1.coordinates[0,2] = 0.25
    sys1.update_chk('coordinates')
    del sys1
    sys1 = System.from_file(chk)
    assert (sys1.numbers != [3, 2]).all()
    assert sys1.coordinates[0,2] == 0.25
    chk.close()
