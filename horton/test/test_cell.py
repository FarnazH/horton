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


import numpy as np
from horton import *

from horton.test.common import get_random_cell


def check_frac_cart(cell):
    cart1 = np.random.uniform(-20, 20, 3)
    frac1 = cell.to_frac(cart1)
    cart2 = cell.to_cart(frac1)
    frac2 = cell.to_frac(cart2)
    print cart1
    print frac1
    print cart2
    assert abs(cart1 - cart2).max() < 1e-10
    assert abs(frac1 - frac2).max() < 1e-10


def test_cell_cubic():
    cell = Cell(np.array([[9.865, 0.0, 0.0], [0.0, 9.865, 0.0], [0.0, 0.0, 9.865]])*angstrom)

    # Test attributes
    assert cell.nvec == 3
    assert (cell.rspacings == 9.865*angstrom).all()
    assert (cell.gspacings == 1/(9.865*angstrom)).all()
    assert abs(cell.volume - (9.865*angstrom)**3) < 1e-10
    assert abs(np.dot(cell.gvecs, cell.rvecs.transpose()) - np.identity(3)).max() < 1e-5
    assert abs(np.dot(cell.gvecs.transpose(), cell.rvecs) - np.identity(3)).max() < 1e-5
    cell2 = Cell(-cell.rvecs)
    assert abs(cell2.volume - (9.865*angstrom)**3) < 1e-10
    for i in xrange(3):
        assert cell.get_rlength(i) == cell.rlengths[i]
        assert cell.get_glength(i) == cell.glengths[i]
        assert cell.get_rspacing(i) == cell.rspacings[i]
        assert cell.get_gspacing(i) == cell.gspacings[i]
        assert abs(cell.get_rlength(i) - 1.0/cell.get_gspacing(i)) < 1e-10
        assert abs(cell.get_glength(i) - 1.0/cell.get_rspacing(i)) < 1e-10

    # Test methods (1)
    vec1 = np.array([10.0, 0.0, 5.0])*angstrom
    cell.mic(vec1)
    assert abs(vec1 - np.array([0.135, 0.0, -4.865])*angstrom).max() < 1e-10
    vec2 = np.array([10.0, 0.0, 5.0])*angstrom
    cell.add_vec(vec2, cell.to_center(vec2))
    assert abs(vec1 - vec2).max() < 1e-10
    cell.add_vec(vec1, np.array([1,2,3]))
    assert abs(vec1 - np.array([10.0, 19.73, 24.73])*angstrom).max() < 1e-10

    # Test methods (2)
    check_frac_cart(cell)


def test_cell_parallellogram2d():
    cell = Cell(np.array([[4.922, 0.0, 0.0], [2.462, 4.262, 0.0]])*angstrom)

    # Test attributes
    assert cell.nvec == 2
    assert abs(cell.volume - np.linalg.norm(np.cross(cell.rvecs[0], cell.rvecs[1]))) < 1e-10
    assert abs(np.dot(cell.gvecs, cell.rvecs.transpose()) - np.identity(2)).max() < 1e-5
    for i in xrange(2):
        assert cell.get_rlength(i) == cell.rlengths[i]
        assert cell.get_glength(i) == cell.glengths[i]
        assert cell.get_rspacing(i) == cell.rspacings[i]
        assert cell.get_gspacing(i) == cell.gspacings[i]
        assert abs(cell.get_rlength(i) - 1.0/cell.get_gspacing(i)) < 1e-10
        assert abs(cell.get_glength(i) - 1.0/cell.get_rspacing(i)) < 1e-10
    assert abs(cell.get_rlength(2) - 1.0) < 1e-10
    assert abs(cell.get_glength(2) - 1.0) < 1e-10
    assert abs(cell.get_rspacing(2) - 1.0) < 1e-10
    assert abs(cell.get_gspacing(2) - 1.0) < 1e-10

    # Test methods (1)
    vec1 = np.array([10.0, 0.0, 105.0])*angstrom
    cell.mic(vec1)
    assert abs(vec1 - np.array([0.156, 0.0, 105])*angstrom).max() < 1e-3
    vec2 = np.array([10.0, 0.0, 105.0])*angstrom
    cell.add_vec(vec2, cell.to_center(vec2))
    assert abs(vec1 - vec2).max() < 1e-10
    cell.add_vec(vec1, np.array([1,2]))
    assert abs(vec1 - np.array([10.002, 8.524, 105])*angstrom).max() < 1e-3

    # Test methods (2)
    check_frac_cart(cell)


def test_cell_1d():
    cell = Cell(np.array([[5.075, 0.187, 0.055]])*angstrom)

    # Test attributes
    assert cell.nvec == 1
    assert cell.rvecs.shape == (1, 3)
    assert cell.gvecs.shape == (1, 3)
    assert abs(cell.volume - np.linalg.norm(cell.rvecs[0])) < 1e-10
    assert abs(np.dot(cell.gvecs, cell.rvecs.transpose()) - 1) < 1e-5
    assert cell.get_rlength(0) == cell.rlengths[0]
    assert cell.get_glength(0) == cell.glengths[0]
    assert cell.get_rspacing(0) == cell.rspacings[0]
    assert cell.get_gspacing(0) == cell.gspacings[0]
    assert abs(cell.get_rlength(0) - 1.0/cell.get_gspacing(0)) < 1e-10
    assert abs(cell.get_glength(0) - 1.0/cell.get_rspacing(0)) < 1e-10
    for i in xrange(1,3):
        assert abs(cell.get_rlength(i) - 1.0) < 1e-10
        assert abs(cell.get_glength(i) - 1.0) < 1e-10
        assert abs(cell.get_rspacing(i) - 1.0) < 1e-10
        assert abs(cell.get_gspacing(i) - 1.0) < 1e-10
    assert abs(cell.get_rspacing(0)*cell.get_gspacing(0) - 1.0) < 1e-10

    # Test methods (1)
    vec1 = np.array([10.0, 0.0, 105.0])*angstrom
    cell.mic(vec1)
    assert abs(vec1 - np.array([-0.15, -0.374, 104.89])*angstrom).max() < 1e-3
    vec2 = np.array([10.0, 0.0, 105.0])*angstrom
    cell.add_vec(vec2, cell.to_center(vec2))
    assert abs(vec1 - vec2).max() < 1e-10
    cell.add_vec(vec1, np.array([1]))
    assert abs(vec1 - np.array([4.925, -0.187, 104.945])*angstrom).max() < 1e-3

    # Test methods (2)
    check_frac_cart(cell)


def test_cell_quartz():
    cell = Cell(np.array([[0.0, 0.0, 5.405222], [0.0, 4.913416, 0.0], [-4.255154, 2.456708, 0.0]])*angstrom)

    # Test attributes
    assert cell.rvecs.shape == (3, 3)
    assert cell.gvecs.shape == (3, 3)
    assert abs(cell.volume - abs(np.linalg.det(cell.rvecs))) < 1e-10
    assert abs(np.dot(cell.gvecs, cell.rvecs.transpose()) - np.identity(3)).max() < 1e-5
    for i in xrange(3):
        assert cell.get_rlength(i) == cell.rlengths[i]
        assert cell.get_glength(i) == cell.glengths[i]
        assert cell.get_rspacing(i) == cell.rspacings[i]
        assert cell.get_gspacing(i) == cell.gspacings[i]
        assert abs(cell.get_rlength(i) - 1.0/cell.get_gspacing(i)) < 1e-10
        assert abs(cell.get_glength(i) - 1.0/cell.get_rspacing(i)) < 1e-10

    # Test methods (2)
    check_frac_cart(cell)

    # Test domain errors
    for i in -1, 4, 245:
        try:
            cell.get_rspacing(i)
            assert False
        except ValueError:
            pass

        try:
            cell.get_gspacing(i)
            assert False
        except ValueError:
            pass


def test_cell_0d():
    cell = Cell()

    # Test attributes
    assert cell.nvec == 0
    assert cell.rvecs.shape == (0, 3)
    assert cell.gvecs.shape == (0, 3)
    assert cell.rspacings.shape == (0,)
    assert cell.gspacings.shape == (0,)
    for i in xrange(3):
        assert abs(cell.get_rlength(i) - 1.0) < 1e-10
        assert abs(cell.get_glength(i) - 1.0) < 1e-10
        assert abs(cell.get_rspacing(i) - 1.0) < 1e-10
        assert abs(cell.get_gspacing(i) - 1.0) < 1e-10

    # Test methods (1)
    vec1 = np.array([10.0, 0.0, 105.0])*angstrom
    cell.mic(vec1)
    assert abs(vec1 - np.array([10.0, 0.0, 105.0])*angstrom).max() < 1e-3
    vec2 = np.array([10.0, 0.0, 105.0])*angstrom
    cell.add_vec(vec2, cell.to_center(vec2))
    assert abs(vec1 - vec2).max() < 1e-10
    cell.add_vec(vec1, np.array([], dtype=int))
    assert abs(vec1 - np.array([10.0, 0.0, 105.0])*angstrom).max() < 1e-3

    # Test methods (2)
    check_frac_cart(cell)


def setup_ranges_rcut(nvec):
    a = 10**np.random.uniform(-1, 1)
    cell = get_random_cell(a, nvec)

    origin = np.random.uniform(-3*a, 3*a, 3)
    center = np.random.uniform(-3*a, 3*a, 3)
    rcut = np.random.uniform(0.2*a, 5*a)

    ranges_begin, ranges_end = cell.get_ranges_rcut(center-origin, rcut)
    ranges_low = ranges_begin-2
    ranges_high = ranges_end+2

    return cell, origin, center, rcut, ranges_begin, ranges_end, ranges_low, ranges_high


def test_ranges_rcut_3d():
    counter = 0
    while True:
        cell, origin, center, rcut, ranges_begin, ranges_end, ranges_low, ranges_high = setup_ranges_rcut(3)
        npoint = np.product(ranges_high-ranges_low)
        if npoint > 10000:
            continue

        # test if distances to points outside the ranges are always outside rcut
        for i0 in xrange(ranges_low[0], ranges_high[0]):
            for i1 in xrange(ranges_low[1], ranges_high[1]):
                for i2 in xrange(ranges_low[2], ranges_high[2]):
                    if (i0 >= ranges_begin[0] and i0 < ranges_end[0] and
                        i1 >= ranges_begin[1] and i1 < ranges_end[1] and
                        i2 >= ranges_begin[2] and i2 < ranges_end[2]):
                        continue
                    tmp = origin.copy()
                    cell.add_vec(tmp, np.array([i0, i1, i2]))
                    assert np.linalg.norm(tmp - center) > rcut

        counter += 1
        if counter >= 20:
            break


def test_ranges_rcut_2d():
    counter = 0
    while True:
        cell, origin, center, rcut, ranges_begin, ranges_end, ranges_low, ranges_high = setup_ranges_rcut(2)

        # test if distances to points outside the ranges are always outside rcut
        for i0 in xrange(ranges_low[0], ranges_high[0]):
            for i1 in xrange(ranges_low[1], ranges_high[1]):
                if (i0 >= ranges_begin[0] and i0 < ranges_end[0] and
                    i1 >= ranges_begin[1] and i1 < ranges_end[1]):
                    continue
                tmp = origin.copy()
                cell.add_vec(tmp, np.array([i0, i1]))
                assert np.linalg.norm(tmp - center) > rcut

        counter += 1
        if counter >= 50:
            break


def test_ranges_rcut_1d():
    counter = 0
    while True:
        cell, origin, center, rcut, ranges_begin, ranges_end, ranges_low, ranges_high = setup_ranges_rcut(1)

        # test if distances to points outside the ranges are always outside rcut
        for i0 in xrange(ranges_low[0], ranges_high[0]):
            if i0 >= ranges_begin[0] and i0 < ranges_end[0]:
                continue
            tmp = origin.copy()
            cell.add_vec(tmp, np.array([i0]))
            assert np.linalg.norm(tmp - center) > rcut

        counter += 1
        if counter >= 200:
            break


def test_ranges_rcut_0d():
    cell = Cell(None)
    a = 0.25
    origin = np.random.uniform(-3*a, 3*a, 3)
    center = np.random.uniform(-3*a, 3*a, 3)
    rcut = np.random.uniform(0.2*a, 5*a)

    ranges_begin, ranges_end = cell.get_ranges_rcut(center-origin, rcut)
    assert ranges_begin.size == 0
    assert ranges_begin.shape == (0,)
    assert ranges_end.size == 0
    assert ranges_end.shape == (0,)


def test_smart_wrap():
    assert smart_wrap(3, 5, 0) == 3
    assert smart_wrap(7, 5, 0) == -1
    assert smart_wrap(-2, 5, 0) == -1
    assert smart_wrap(3, 5, 1) == 3
    assert smart_wrap(7, 5, 1) == 2
    assert smart_wrap(-2, 5, 1) == 3


def setup_select_inside(nvec):
    a = 10**np.random.uniform(-1, 1)
    grid_cell = get_random_cell(a, nvec)

    nrep = 40
    shape = np.array([nrep]*nvec)
    pbc_active = np.random.randint(0, 2, nvec)
    origin = np.random.uniform(-0.5*nrep*a, 1.5*nrep*a, 3)
    center = np.random.uniform(0, nrep*a, 3)
    rcut = np.random.uniform(0.1*nrep*a)

    ranges_begin, ranges_end = grid_cell.get_ranges_rcut(center-origin, rcut)

    return grid_cell, origin, center, rcut, shape, pbc_active, ranges_begin, ranges_end


def check_select_inside_basic(indexes, shape, origin, center, grid_cell, cell, rcut):
    # assert that the indexes fit in the shape
    assert (indexes >= 0).all()
    assert (indexes < shape).all()

    # assert that all distances (with MIC) are below rcut
    for ifrac in indexes:
        tmp = origin - center
        grid_cell.add_vec(tmp, ifrac)
        cell.mic(tmp)
        assert np.linalg.norm(tmp) < rcut


def test_select_inside_3d():
    counter = 0
    while True:
        grid_cell, origin, center, rcut, shape, pbc_active, ranges_begin, ranges_end = setup_select_inside(3)
        rvecs = (grid_cell.rvecs*shape.reshape(3,1))[pbc_active.astype(bool)]
        cell = Cell(rvecs)
        if cell.nvec > 0 and 2*rcut > cell.rspacings.min():
            continue
        npoint = np.product(ranges_end-ranges_begin)
        if npoint > 10000:
            continue

        # compute the indices inside rcut
        indexes = np.zeros((npoint, 3), int)
        nselect = grid_cell.select_inside(origin, center, rcut, ranges_begin, ranges_end, shape, pbc_active, indexes)
        indexes = indexes[:nselect]

        # elementary tests
        check_select_inside_basic(indexes, shape, origin, center, grid_cell, cell, rcut)

        # count the number of points that fall inside
        ninside = 0
        for i0 in xrange(ranges_begin[0], ranges_end[0]):
            j0 = smart_wrap(i0, shape[0], pbc_active[0])
            if j0 == -1: continue
            for i1 in xrange(ranges_begin[1], ranges_end[1]):
                j1 = smart_wrap(i1, shape[1], pbc_active[1])
                if j1 == -1: continue
                for i2 in xrange(ranges_begin[2], ranges_end[2]):
                    j2 = smart_wrap(i2, shape[2], pbc_active[2])
                    if j2 == -1: continue
                    tmp = origin - center
                    grid_cell.add_vec(tmp, np.array([i0, i1, i2]))
                    ninside += np.linalg.norm(tmp) < rcut

        # number of points inside must match
        assert ninside == len(indexes)

        counter += 1
        if counter >= 100:
            break


def test_select_inside_2d():
    counter = 0
    while True:
        grid_cell, origin, center, rcut, shape, pbc_active, ranges_begin, ranges_end = setup_select_inside(2)
        rvecs = (grid_cell.rvecs*shape.reshape(2,1))[pbc_active.astype(bool)]
        cell = Cell(rvecs)
        if cell.nvec > 0 and 2*rcut > cell.rspacings.min():
            continue
        npoint = np.product(ranges_end-ranges_begin)
        if npoint > 10000:
            continue

        # compute the indices inside rcut
        indexes = np.zeros((npoint, 2), int)
        nselect = grid_cell.select_inside(origin, center, rcut, ranges_begin, ranges_end, shape, pbc_active, indexes)
        indexes = indexes[:nselect]

        # elementary tests
        check_select_inside_basic(indexes, shape, origin, center, grid_cell, cell, rcut)

        # count the number of points that fall inside
        ninside = 0
        for i0 in xrange(ranges_begin[0], ranges_end[0]):
            j0 = smart_wrap(i0, shape[0], pbc_active[0])
            if j0 == -1: continue
            for i1 in xrange(ranges_begin[1], ranges_end[1]):
                j1 = smart_wrap(i1, shape[1], pbc_active[1])
                if j1 == -1: continue
                tmp = origin - center
                grid_cell.add_vec(tmp, np.array([i0, i1]))
                ninside += np.linalg.norm(tmp) < rcut

        # number of points inside must match
        assert ninside == len(indexes)

        counter += 1
        if counter >= 200:
            break


def test_select_inside_1d():
    counter = 0
    while True:
        grid_cell, origin, center, rcut, shape, pbc_active, ranges_begin, ranges_end = setup_select_inside(1)
        rvecs = (grid_cell.rvecs*shape)[pbc_active.astype(bool)]
        cell = Cell(rvecs)
        if cell.nvec > 0 and 2*rcut > cell.rspacings.min():
            continue
        npoint = np.product(ranges_end-ranges_begin)
        if npoint > 10000:
            continue

        # compute the indices inside rcut
        indexes = np.zeros((npoint, 1), int)
        nselect = grid_cell.select_inside(origin, center, rcut, ranges_begin, ranges_end, shape, pbc_active, indexes)
        indexes = indexes[:nselect]

        # elementary tests
        check_select_inside_basic(indexes, shape, origin, center, grid_cell, cell, rcut)

        # count the number of points that fall inside
        ninside = 0
        for i0 in xrange(ranges_begin[0], ranges_end[0]):
            j0 = smart_wrap(i0, shape[0], pbc_active[0])
            if j0 == -1: continue
            tmp = origin - center
            grid_cell.add_vec(tmp, np.array([i0]))
            ninside += np.linalg.norm(tmp) < rcut

        # number of points inside must match
        assert ninside == len(indexes)

        counter += 1
        if counter >= 200:
            break


def test_select_inside_0d():
    grid_cell, origin, center, rcut, shape, pbc_active, ranges_begin, ranges_end = setup_select_inside(0)
    npoint = np.product(ranges_end-ranges_begin)
    indexes = np.zeros((npoint, 0), int)
    try:
        nselect = grid_cell.select_inside(origin, center, rcut, ranges_begin, ranges_end, shape, pbc_active, indexes)
        assert False
    except ValueError:
        pass
