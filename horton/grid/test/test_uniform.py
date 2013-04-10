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
from horton.grid.test.common import *
from horton.test.common import get_random_cell


def test_uig_integrate_gauss():
    # grid parameters
    spacing = 0.1
    naxis = 81

    # grid setup
    offset = 0.5*spacing*(naxis-1)
    origin = np.zeros(3, float)-offset
    rvecs = np.identity(3)*spacing
    shape = np.array([naxis, naxis, naxis])
    pbc = np.ones(3, int)
    uig = UniformIntGrid(origin, rvecs, shape, pbc)

    # fill a 3D grid with a gaussian function
    x, y, z = np.indices(shape)
    dsq = (x*spacing-offset)**2 + (y*spacing-offset)**2 + (z*spacing-offset)**2
    data = np.exp(-0.5*dsq)/(2*np.pi)**(1.5)

    # compute the integral and compare with analytical result
    num_result = uig.integrate(data)
    assert abs(num_result - 1.0) < 1e-3


def test_index_wrap():
    assert index_wrap(2, 3) == 2
    assert index_wrap(-5, 10) == 5
    assert index_wrap(5, 10) == 5
    assert index_wrap(15, 10) == 5


def test_uig_eval_spline_simple1():
    cs = get_cosine_spline()
    offset = 5.0
    spacing = 0.5
    uig = UniformIntGrid(np.array([-offset, -offset, -offset]), np.identity(3)*spacing, np.array([21,21,21]), np.array([1, 1, 1]))

    x, y, z = np.indices(uig.shape)
    d = np.sqrt((x*spacing-offset)**2 + (y*spacing-offset)**2 + (z*spacing-offset)**2).ravel()
    data1 = cs(d)
    data2 = np.zeros(uig.shape)
    uig.eval_spline(cs, np.zeros(3), data2)
    data2 = data2.ravel()

    assert abs(data1 - data2).max() == 0.0


def test_uig_eval_spline_simple2():
    cs = get_cosine_spline()
    offset = 1.0
    spacing = 0.1
    uig = UniformIntGrid(np.array([-offset, -offset, -offset]), np.identity(3)*spacing, np.array([21,21,21]), np.array([1, 1, 1]))

    x, y, z = np.indices(uig.shape)
    data1 = 0
    for ix in xrange(-1,2):
        for iy in xrange(-1,2):
            for iz in xrange(-1,2):
                d = np.sqrt((x*spacing-offset+ix*2.1)**2 + (y*spacing-offset+iy*2.1)**2 + (z*spacing-offset+iz*2.1)**2).ravel()
                data1 += cs(d)

    data2 = np.zeros(uig.shape)
    uig.eval_spline(cs, np.zeros(3), data2)
    data2 = data2.ravel()

    assert abs(data1 - data2).max() < 1e-12


def test_uig_eval_spline_with_integration():
    cs = get_cosine_spline()

    # Different integration grids
    pbc = np.ones(3, int)
    uigs = [
        UniformIntGrid(np.array([-1.0, -1.0, -1.0]), np.identity(3)*0.1, np.array([21,21,21]), pbc),
        UniformIntGrid(np.array([-1.0, -1.0, -1.0]), np.array([[0.1, 0.1, 0.0], [0.1, 0.0, 0.1], [0.0, 0.1, 0.1]]), np.array([21,21,21]), pbc),
        UniformIntGrid(np.array([0.0, 0.0, 0.0]), np.identity(3)*0.1, np.array([21,21,21]), pbc),
        UniformIntGrid(np.array([0.0, 0.0, 0.0]), np.array([[0.1, 0.1, 0.0], [0.1, 0.0, 0.1], [0.0, 0.1, 0.1]]), np.array([21,21,21]), pbc),
        UniformIntGrid(np.array([0.0, 0.0, 0.0]), np.array([[0.1471, 0.0745, -0.010], [0.0315, -0.1403, 0.1], [0.0014, 0.147, 0.0]]), np.array([21,21,21]), pbc),
    ]

    for uig in uigs:
        # fill a 3D grid with the cosine test function
        data = np.zeros(uig.shape)
        uig.eval_spline(cs, np.zeros(3), data)

        # test the integral
        expected = 4*np.pi**2*(np.pi**2/3-2)
        assert abs(uig.integrate(data) - expected) < 1e-3


def test_uig_eval_spline_3d_random():
    cs = get_cosine_spline()

    for i in xrange(10):
        origin = np.random.uniform(-1, 1, 3)
        grid_cell = get_random_cell(0.3, 3)
        shape = np.random.randint(10, 20, 3)
        pbc = np.array([1, 1, 1])
        uig = UniformIntGrid(origin, grid_cell.rvecs, shape, pbc)

        rvecs = grid_cell.rvecs*uig.shape.reshape(-1,1)

        output1 = np.zeros(uig.shape)
        center1 = np.random.uniform(-3, 3, 3)
        uig.eval_spline(cs, center1, output1)
        output2 = np.zeros(uig.shape)
        center2 = center1 + np.dot(np.random.randint(-3, 3, 3), rvecs)
        uig.eval_spline(cs, center2, output2)

        assert abs(output1 - output2).max() < 1e-10


def test_uig_eval_spline_2d_random():
    cs = get_cosine_spline()

    for i in xrange(15):
        origin = np.random.uniform(-1, 1, 3)
        grid_cell = get_random_cell(0.2, 3)
        shape = np.random.randint(10, 20, 3)
        pbc = np.array([1, 1, 1])
        pbc[np.random.randint(3)] = 0
        uig = UniformIntGrid(origin, grid_cell.rvecs, shape, pbc)

        tmp = uig.shape*pbc
        rvecs = grid_cell.rvecs*tmp.reshape(-1,1)

        output1 = np.zeros(uig.shape)
        center1 = np.random.uniform(0, 1, 3)
        uig.eval_spline(cs, center1, output1)
        output2 = np.zeros(uig.shape)
        center2 = center1 + np.dot(np.random.randint(-3, 3, 3), rvecs)
        uig.eval_spline(cs, center2, output2)

        assert abs(output1 - output2).max() < 1e-10


def test_uig_eval_spline_0d_random():
    cs = get_cosine_spline()

    for i in xrange(15):
        origin = np.random.uniform(-1, 1, 3)
        grid_cell = get_random_cell(0.2, 3)
        shape = np.random.randint(10, 20, 3)
        pbc = np.array([0, 0, 0])
        uig = UniformIntGrid(origin, grid_cell.rvecs, shape, pbc)

        center = np.random.uniform(0, 2, 3)
        output1 = np.zeros(uig.shape)
        uig.eval_spline(cs, center, output1)

        x, y, z = np.indices(shape)
        x = x.ravel()
        y = y.ravel()
        z = z.ravel()
        rvecs = grid_cell.rvecs
        points = np.outer(x, rvecs[0]) + np.outer(y, rvecs[1]) + np.outer(z, rvecs[2])
        points += origin
        distances = np.zeros(len(points))
        grid_distances(points, center, distances)
        output2 = cs(distances)
        output2.shape = shape

        assert abs(output1 - output2).max() < 1e-10


def test_uig_eval_spline_1d_random():
    cs = get_cosine_spline()

    for i in xrange(15):
        origin = np.random.uniform(-1, 1, 3)
        grid_cell = get_random_cell(0.2, 3)
        shape = np.random.randint(10, 20, 3)
        pbc = np.array([0, 0, 0])
        pbc[np.random.randint(3)] = 1
        uig = UniformIntGrid(origin, grid_cell.rvecs, shape, pbc)

        tmp = uig.shape*pbc
        rvecs = grid_cell.rvecs*tmp.reshape(-1,1)

        output1 = np.zeros(uig.shape)
        center1 = np.random.uniform(0, 1, 3)
        uig.eval_spline(cs, center1, output1)
        output2 = np.zeros(uig.shape)
        center2 = center1 + np.dot(np.random.randint(-3, 3, 3), rvecs)
        uig.eval_spline(cs, center2, output2)

        assert abs(output1 - output2).max() < 1e-10


def test_uig_eval_spline_add_random():
    cs = get_cosine_spline()

    for i in xrange(20):
        origin = np.random.uniform(-1, 1, 3)
        grid_cell = get_random_cell(0.2, 3)
        shape = np.random.randint(10, 20, 3)
        pbc = np.random.randint(0, 2, 3).astype(int)
        uig = UniformIntGrid(origin, grid_cell.rvecs, shape, pbc)

        output1 = np.zeros(uig.shape)
        center1 = np.random.uniform(0, 1, 3)
        uig.eval_spline(cs, center1, output1)

        output2 = np.zeros(uig.shape)
        center2 = np.random.uniform(0, 1, 3)
        uig.eval_spline(cs, center2, output2)

        output3 = np.zeros(uig.shape)
        uig.eval_spline(cs, center1, output3)
        uig.eval_spline(cs, center2, output3)

        assert abs(output1 + output2 - output3).max() < 1e-10


def test_weight_corrections():
    from horton.cpart.test.common import get_fake_co

    sys, ui_grid, mol_dens, proatomdb = get_fake_co()

    funcs = [
        (sys.coordinates[0], [
            #proatomdb.get_spline(6, +1),
            proatomdb.get_spline(6,  0),
            #proatomdb.get_spline(6, -1),
        ]),
        (sys.coordinates[1], [
            #proatomdb.get_spline(8, +1),
            proatomdb.get_spline(8,  0),
            #proatomdb.get_spline(8, -1),
        ]),
    ]
    weights = ui_grid.compute_weight_corrections(funcs)
    assert (weights != 1.0).any()
    assert (weights == 1.0).any()

    assert abs(ui_grid.integrate(mol_dens, weights)-14.0) < 6e-3
    assert abs(ui_grid.integrate(mol_dens)-14.0) > 5e-2


def get_simple_test_uig():
    origin = np.array([0.1, -2.0, 3.1])
    rvecs = np.array([
        [1.0, 0.1, 0.2],
        [0.1, 1.1, 0.2],
        [0.0, -0.1, 1.0],
    ])
    #origin = np.array([0.0, 0.0, 0.0])
    #rvecs = np.array([
    #    [1.0, 0.0, 0.0],
    #    [0.0, 1.0, 0.0],
    #    [0.0, 0.0, 1.0],
    #])
    shape = np.array([40, 40, 40])
    pbc = np.array([1, 0, 1])
    return UniformIntGrid(origin, rvecs, shape, pbc)


def test_get_ranges_rcut1():
    uig = get_simple_test_uig()
    center = np.array([0.1, -2.5, 3.2])
    rb1, re1 = uig.get_ranges_rcut(center, 2.0)
    rb2, re2 = uig.grid_cell.get_ranges_rcut(uig.origin - center, 2.0)
    assert rb1[0] == rb2[0]
    assert rb1[1] == 0
    assert rb1[2] == rb2[2]
    assert (re1 == re2).all()


def test_get_ranges_rcut2():
    uig = get_simple_test_uig()
    center = np.array([60.0, 50.0, 60.0])
    rb1, re1 = uig.get_ranges_rcut(center, 2.0)
    rb2, re2 = uig.grid_cell.get_ranges_rcut(uig.origin - center, 2.0)
    assert (rb1 == rb2).all()
    assert re1[0] == re2[0]
    assert re1[1] == 40
    assert re1[2] == re2[2]


def test_dist_grid_point():
    uig = get_simple_test_uig()
    assert uig.dist_grid_point(uig.origin, np.array([0, 0, 0])) == 0.0
    assert uig.dist_grid_point(uig.origin, np.array([0, 0, 1])) == (0.1**2+1.0)**0.5
    assert uig.dist_grid_point(uig.origin, np.array([0, 1, 0])) == (0.1**2+1.1**2+0.2**2)**0.5

    center = np.array([0.9, 2.5, 1.6])
    indexes = np.array([6, 3, -2])
    point = uig.origin + uig.grid_cell.to_cart(indexes.astype(float))
    assert abs(uig.dist_grid_point(center, np.array([6, 3, -2])) - np.linalg.norm(center - point)) < 1e-10


def test_delta_grid_point():
    uig = get_simple_test_uig()
    assert (uig.delta_grid_point(uig.origin, np.array([0, 0, 0])) == np.array([0.0, 0.0, 0.0])).all()
    assert (uig.delta_grid_point(uig.origin, np.array([0, 0, 1])) == np.array([0.0, -0.1, 1.0])).all()
    assert (uig.delta_grid_point(uig.origin, np.array([0, 1, 0])) == np.array([0.1, 1.1, 0.2])).all()

    center = np.array([0.9, 2.5, 1.6])
    indexes = np.array([6, 3, -2])
    point = uig.origin + uig.grid_cell.to_cart(indexes.astype(float))
    assert abs(uig.delta_grid_point(center, np.array([6, 3, -2])) - (point - center)).max() < 1e-10


def test_window3_extend_simple1():
    origin = np.zeros(3, float)
    grid_rvecs = np.identity(3, float)*0.1
    shape = np.array([2, 3, 4])
    pbc = np.array([1, 1, 1])
    ui_grid = UniformIntGrid(origin, grid_rvecs, shape, pbc)

    # test for get_window
    window = UniformIntGridWindow(ui_grid, np.array([0, 0, 0]), shape)

    # test for extend method
    small = np.random.uniform(0, 1, ui_grid.shape)
    big = window.zeros()
    assert small.shape == big.shape
    window.extend(small, big)
    assert (big == small).all()


def test_window3_extend_simple2():
    origin = np.zeros(3, float)
    grid_rvecs = np.identity(3, float)*0.1
    shape = np.array([2, 3, 4])
    pbc = np.array([1, 1, 1])
    ui_grid = UniformIntGrid(origin, grid_rvecs, shape, pbc)

    # test for get_window
    window = UniformIntGridWindow(ui_grid, np.array([1, 1, 1]), shape)

    # test for extend method
    small = np.random.uniform(0, 1, ui_grid.shape)
    big = window.zeros()
    for i in xrange(3):
        assert small.shape[i]-1 == big.shape[i]
    window.extend(small, big)
    assert (big == small[1:,1:,1:]).all()


def check_window_block(small, big, window, shape, i0, i1, i2):
    offset = shape*[i0, i1, i2]
    # without clipping
    begin = offset.copy()
    end = begin + shape
    # apply clipping
    mask = begin<window.begin
    begin[mask] = window.begin[mask]
    mask = end>window.end
    end[mask] = window.end[mask]
    # test if this iteration has any grid points to be tested
    if (end <= begin).any():
        return
    # actual comparison
    begin1 = begin - window.begin
    end1 = end - window.begin
    big_block = big[begin1[0]:end1[0], begin1[1]:end1[1], begin1[2]:end1[2]]
    begin2 = begin - offset
    end2 = end - offset
    small_block = small[begin2[0]:end2[0], begin2[1]:end2[1], begin2[2]:end2[2]]
    assert (big_block == small_block).all()


def check_window_ui_grid(window):
    ui_grid = window.get_window_ui_grid()
    assert abs(ui_grid.origin - (window.ui_grid.origin + np.dot(window.begin, ui_grid.grid_cell.rvecs))).max() < 1e-10
    assert ui_grid.grid_cell.nvec == 3
    assert (ui_grid.grid_cell.rvecs == window.ui_grid.grid_cell.rvecs).all()
    assert (ui_grid.shape == window.end - window.begin).all()
    assert (ui_grid.pbc == 0).all()


def helper_xyzr_window(window, center):
    origin = window.ui_grid.origin
    grid_rvecs = window.ui_grid.grid_cell.rvecs
    indexes = np.indices(window.shape)
    indexes += window.begin.reshape(3, 1, 1, 1)
    x = (origin[0] + indexes[0]*grid_rvecs[0,0] + indexes[1]*grid_rvecs[1,0] + indexes[2]*grid_rvecs[2,0]) - center[0]
    y = (origin[1] + indexes[0]*grid_rvecs[0,1] + indexes[1]*grid_rvecs[1,1] + indexes[2]*grid_rvecs[2,1]) - center[1]
    z = (origin[2] + indexes[0]*grid_rvecs[0,2] + indexes[1]*grid_rvecs[1,2] + indexes[2]*grid_rvecs[2,2]) - center[2]
    r = (x*x + y*y + z*z)**0.5
    return x, y, z, r


def check_integrate_poly(window, center, big):
    x, y, z, r = helper_xyzr_window(window, center)
    for i in xrange(10):
        nx = np.random.randint(5)
        ny = np.random.randint(5)
        nz = np.random.randint(5)
        nr = np.random.randint(5)
        value = window.integrate(big, center=center, nx=nx, ny=ny, nz=nz, nr=nr)
        expected = window.integrate(big, x**nx, y**ny, z**nz, r**nr)
        assert value != 0
        assert abs(value - expected) < 1e-10


def check_window_eval_spline(window, center, radius):
    # construct a random spline
    npoint = 5
    rtf = LinearRTransform(0.001, radius, npoint)
    spline = CubicSpline(np.random.uniform(0, 1, npoint), rtf=rtf)

    # test the routine
    x, y, z, r = helper_xyzr_window(window, center)
    output = window.zeros()
    window.eval_spline(spline, center, output)
    values = output.ravel()
    expected = spline(r.ravel())
    assert values.max() > 0
    assert values.min() == 0
    assert abs(values - expected).max() < 1e-10


def test_window3():
    origin = np.zeros(3, float)
    grid_rvecs = np.identity(3, float)*0.1
    shape = np.array([5, 10, 15])
    pbc = np.array([1, 1, 1])
    ui_grid = UniformIntGrid(origin, grid_rvecs, shape, pbc)

    # test for get_window
    center = np.array([0.25, 0.0, -0.8])
    radius = 1.3
    window = ui_grid.get_window(center, radius)

    assert (window.begin == [-10, -13, -21]).all()
    assert (window.end == [16, 13, 5]).all()

    # test for extend method
    small = np.random.uniform(0, 1, ui_grid.shape)
    big = window.zeros()
    window.extend(small, big)

    assert (big != 0.0).any()
    for i0 in xrange(-2, 3):
        for i1 in xrange(-2, 3):
            for i2 in xrange(-2, 3):
                check_window_block(small, big, window, shape, i0, i1, i2)

    # test for get_window_ui_grid
    check_window_ui_grid(window)

    # test for integrate
    assert abs(window.integrate(big) - big.sum()*ui_grid.grid_cell.volume) < 1e-10

    # test for integrate with poly
    check_integrate_poly(window, center, big)

    # test for eval_spline
    check_window_eval_spline(window, center, radius)


def test_window2():
    origin = np.array([-0.3, 0.22, 0.0])
    grid_rvecs = np.identity(3, float)*0.1
    shape = np.array([5, 10, 15])
    pbc = np.array([1, 1, 0])
    ui_grid = UniformIntGrid(origin, grid_rvecs, shape, pbc)

    # test for get_window
    center = np.array([0.25, 0.0, -0.8])
    radius = 1.4
    window = ui_grid.get_window(center, radius)

    assert (window.begin == [-8, -16, 0]).all()
    assert (window.end == [20, 12, 6]).all()

    # test for extend method
    small = np.random.uniform(0, 1, ui_grid.shape)
    big = window.zeros()
    window.extend(small, big)

    assert (big[:,:,:6] != 0.0).any()
    assert (big[:,:,6:] == 0.0).all()
    for i0 in xrange(-2, 3):
        for i1 in xrange(-2, 3):
            check_window_block(small, big, window, shape, i0, i1, 0)

    # test for get_window_ui_grid
    check_window_ui_grid(window)

    # test for integrate
    assert abs(window.integrate(big) - big.sum()*ui_grid.grid_cell.volume) < 1e-10

    # test for integrate with poly
    check_integrate_poly(window, center, big)

    # test for eval_spline
    check_window_eval_spline(window, center, radius)


def test_window1():
    origin = np.array([-0.3, 0.22, 0.0])
    grid_rvecs = np.identity(3, float)*0.1
    shape = np.array([5, 10, 15])
    pbc = np.array([1, 0, 0])
    ui_grid = UniformIntGrid(origin, grid_rvecs, shape, pbc)

    # test for get_window
    center = np.array([0.25, 0.0, -0.8])
    radius = 1.4
    window = ui_grid.get_window(center, radius)

    assert (window.begin == [-8, 0, 0]).all()
    assert (window.end == [20, 10, 6]).all()

    # test for extend method
    small = np.random.uniform(0, 1, ui_grid.shape)
    big = window.zeros()
    window.extend(small, big)

    assert (big[:,:,:6] != 0.0).any()
    assert (big[:,:,6:] == 0.0).all()
    for i0 in xrange(-2, 3):
        check_window_block(small, big, window, shape, i0, 0, 0)

    # test for get_window_ui_grid
    check_window_ui_grid(window)

    # test for integrate
    assert abs(window.integrate(big) - big.sum()*ui_grid.grid_cell.volume) < 1e-10

    # test for integrate with poly
    check_integrate_poly(window, center, big)

    # test for eval_spline
    check_window_eval_spline(window, center, radius)


def test_window0():
    origin = np.array([-0.3, 0.22, 0.0])
    grid_rvecs = np.identity(3, float)*0.1
    shape = np.array([5, 10, 15])
    pbc = np.array([0, 0, 0])
    ui_grid = UniformIntGrid(origin, grid_rvecs, shape, pbc)

    # test for get_window
    center = np.array([0.25, 0.0, -0.8])
    radius = 1.4
    window = ui_grid.get_window(center, radius)

    assert (window.begin == [0, 0, 0]).all()
    assert (window.end == [5, 10, 6]).all()

    # test for extend method
    small = np.random.uniform(0, 1, ui_grid.shape)
    big = window.zeros()
    window.extend(small, big)

    assert (big[:,:,:6] != 0.0).any()
    assert (big[:,:,6:] == 0.0).all()
    check_window_block(small, big, window, shape, 0, 0, 0)

    # test for get_window_ui_grid
    check_window_ui_grid(window)

    # test for integrate
    assert abs(window.integrate(big) - big.sum()*ui_grid.grid_cell.volume) < 1e-10

    # test for integrate with poly
    check_integrate_poly(window, center, big)

    # test for eval_spline
    check_window_eval_spline(window, center, radius)
