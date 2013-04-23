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
from horton.log import log


cimport numpy as np
np.import_array()

from libc.stdlib cimport malloc, free

cimport lebedev_laikov
cimport becke
cimport cubic_spline
cimport evaluate
cimport rtransform
cimport uniform
cimport utils

cimport horton.cext


# TODO: make extension types (un)picklable
# See https://groups.google.com/forum/?fromgroups=#!topic/cython-users/vzG58m0Yr2Y

__all__ = [
    # lebedev_laikov
    'lebedev_laikov_npoint', 'lebedev_laikov_sphere', 'lebedev_laikov_npoints',
    # becke
    'becke_helper_atom',
    # cubic_spline
    'tridiag_solve', 'tridiagsym_solve', 'CubicSpline',
    'compute_cubic_spline_int_weights',
    # evaluate
    'index_wrap', 'eval_spline_cube', 'eval_spline_grid',
    # rtransform
    'RTransform', 'IdentityRTransform', 'LinearRTransform', 'ExpRTransform',
    'ShiftedExpRTransform', 'BakerRTransform',
    # UniformIntGrid
    'UniformIntGrid', 'UniformIntGridWindow', 'index_wrap', 'Block3Iterator',
    # utils
    'dot_multi', 'dot_multi_moments_cube', 'grid_distances',
]


#
# lebedev_laikov
#


lebedev_laikov_npoints = [6, 14, 26, 38, 50, 74, 86, 110, 146, 170, 194, 230,
                          266, 302, 350, 434, 590, 770, 974, 1202, 1454, 1730,
                          2030, 2354, 2702, 3074, 3470, 3890, 4334, 4802, 5294,
                          5810]


def lebedev_laikov_npoint(int lvalue):
    '''lebedev_laikov_npoint(lvalue)

       Return the number of Lebedev-Laikov grid points for a given angular
       momentum.
    '''
    return lebedev_laikov.lebedev_laikov_npoint(lvalue)


def lebedev_laikov_sphere(np.ndarray[double, ndim=2] points,
                          np.ndarray[double, ndim=1] weights):
    '''lebedev_laikov_sphere(grid)

       Fill the grid with a Lebedev Laikov grid points of a given size.

       **Arguments:**

       points
            The output array for the grid points, shape (npoint,3).

       weights
            The output array for the grid weights, shape (npoint,).
    '''
    assert points.flags['C_CONTIGUOUS']
    assert points.shape[1] == 3
    npoint = points.shape[0]
    assert weights.flags['C_CONTIGUOUS']
    assert weights.shape[0] == npoint
    lebedev_laikov.lebedev_laikov_sphere(npoint, <double*>points.data,
                                         <double*>weights.data)


#
# becke
#


def becke_helper_atom(np.ndarray[double, ndim=2] points,
                      np.ndarray[double, ndim=1] weights,
                      np.ndarray[double, ndim=1] radii,
                      np.ndarray[double, ndim=2] centers,
                      int select, int order):
    '''beck_helper_atom(points, weights, radii, centers, i, k)

       Compute the Becke weights for a given atom an a grid.

       **Arguments:**

       points
            The Cartesian coordinates of the grid points. Numpy array with
            shape (npoint, 3)

       weights
            The output array where the Becke partitioning weights are written.
            Numpy array with shape (npoint,)

       radii
            The covalent radii used to shrink/enlarge basins in the Becke
            scheme.

       centers
            The positions of the nuclei.

       select
            The selected atom for which the weights should be created.

       order
            The order of the switching functions. (That is k in Becke's paper.)

       See Becke's paper for the details: http://dx.doi.org/10.1063/1.454033
    '''
    assert points.flags['C_CONTIGUOUS']
    assert points.shape[1] == 3
    npoint = points.shape[0]
    assert weights.flags['C_CONTIGUOUS']
    assert weights.shape[0] == npoint
    assert radii.flags['C_CONTIGUOUS']
    natom = radii.shape[0]
    assert centers.flags['C_CONTIGUOUS']
    assert centers.shape[0] == natom
    assert centers.shape[1] == 3
    assert select >= 0 and select < natom
    assert order > 0

    becke.becke_helper_atom(points.shape[0], <double*>points.data,
                            <double*>weights.data, natom, <double*>radii.data,
                            <double*>centers.data, select, order)


#
# cubic_spline
#


def tridiag_solve(np.ndarray[double, ndim=1] diag_low,
                  np.ndarray[double, ndim=1] diag_mid,
                  np.ndarray[double, ndim=1] diag_up,
                  np.ndarray[double, ndim=1] right,
                  np.ndarray[double, ndim=1] solution):
    assert diag_mid.flags['C_CONTIGUOUS']
    n = diag_mid.shape[0]
    assert n > 1
    assert diag_low.flags['C_CONTIGUOUS']
    assert diag_low.shape[0] == n-1
    assert diag_up.flags['C_CONTIGUOUS']
    assert diag_up.shape[0] == n-1
    assert right.flags['C_CONTIGUOUS']
    assert right.shape[0] == n
    assert solution.flags['C_CONTIGUOUS']
    assert solution.shape[0] == n
    cubic_spline.tridiag_solve(<double*>diag_low.data, <double*>diag_mid.data,
                               <double*>diag_up.data, <double*>right.data,
                               <double*>solution.data, n)


def tridiagsym_solve(np.ndarray[double, ndim=1] diag_mid,
                     np.ndarray[double, ndim=1] diag_up,
                     np.ndarray[double, ndim=1] right,
                     np.ndarray[double, ndim=1] solution):
    assert diag_mid.flags['C_CONTIGUOUS']
    n = diag_mid.shape[0]
    assert n > 1
    assert diag_up.flags['C_CONTIGUOUS']
    assert diag_up.shape[0] == n-1
    assert right.flags['C_CONTIGUOUS']
    assert right.shape[0] == n
    assert solution.flags['C_CONTIGUOUS']
    assert solution.shape[0] == n
    cubic_spline.tridiagsym_solve(<double*>diag_mid.data, <double*>diag_up.data,
                                  <double*>right.data, <double*>solution.data,
                                  n)


cdef class CubicSpline(object):
    cdef cubic_spline.CubicSpline* _this
    cdef cubic_spline.Extrapolation* _ep
    cdef RTransform _rtf

    def __cinit__(self, np.ndarray[double, ndim=1] y not None, np.ndarray[double, ndim=1] d=None, RTransform rtf=None):
        cdef double* ddata
        assert y.flags['C_CONTIGUOUS']
        n = y.shape[0]
        if d is None:
            ddata = <double*>NULL
        else:
            assert d.flags['C_CONTIGUOUS']
            assert d.shape[0] == n
            ddata = <double*>d.data

        self._rtf = rtf
        cdef rtransform.RTransform* _c_rtf
        if rtf is None:
            _c_rtf = NULL
        else:
            _c_rtf = rtf._this
        # Only exponential extrapolation is needed for now, except when it does not work
        if d is not None and d[0] == 0.0:
            self._ep = <cubic_spline.Extrapolation*>(new cubic_spline.ZeroExtrapolation())
        else:
            self._ep = <cubic_spline.Extrapolation*>(new cubic_spline.ExponentialExtrapolation())
        self._this = new cubic_spline.CubicSpline(
            <double*>y.data, ddata, self._ep, _c_rtf, n
        )

    def __dealloc__(self):
        del self._this
        del self._ep

    property rtransform: # TODO: rename to rtf
        def __get__(self):
            return self._rtf

    def copy_y(self):
        cdef np.npy_intp shape[1]
        shape[0] = self._this.n
        tmp = np.PyArray_SimpleNewFromData(1, shape, np.NPY_DOUBLE, <void*> self._this.y)
        return tmp.copy()

    def copy_d(self):
        cdef np.npy_intp shape[1]
        shape[0] = self._this.n
        tmp = np.PyArray_SimpleNewFromData(1, shape, np.NPY_DOUBLE, <void*> self._this.d)
        return tmp.copy()

    def __call__(self, np.ndarray[double, ndim=1] new_x not None, np.ndarray[double, ndim=1] new_y=None):
        assert new_x.flags['C_CONTIGUOUS']
        new_n = new_x.shape[0]
        if new_y is None:
            new_y = np.zeros(new_n, float)
        else:
            assert new_y.flags['C_CONTIGUOUS']
            assert new_y.shape[0] == new_n
        self._this.eval(<double*>new_x.data, <double*>new_y.data, new_n)
        return new_y

    def deriv(self, np.ndarray[double, ndim=1] new_x not None, np.ndarray[double, ndim=1] new_d=None):
        assert new_x.flags['C_CONTIGUOUS']
        new_n = new_x.shape[0]
        if new_d is None:
            new_d = np.zeros(new_n, float)
        else:
            assert new_d.flags['C_CONTIGUOUS']
            assert new_d.shape[0] == new_n
        self._this.eval_deriv(<double*>new_x.data, <double*>new_d.data, new_n)
        return new_d


def compute_cubic_spline_int_weights(np.ndarray[double, ndim=1] weights not None):
    assert weights.flags['C_CONTIGUOUS']
    npoint = weights.shape[0]
    cubic_spline.compute_cubic_spline_int_weights(<double*>weights.data, npoint)


#
# evaluate
#


def index_wrap(long i, long high):
    return evaluate.index_wrap(i, high)


def eval_spline_cube(CubicSpline spline,
                     np.ndarray[double, ndim=1] center,
                     np.ndarray[double, ndim=3] output,
                     UniformIntGrid ui_grid):

    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3
    assert output.flags['C_CONTIGUOUS']
    assert output.shape[0] == ui_grid.shape[0]
    assert output.shape[1] == ui_grid.shape[1]
    assert output.shape[2] == ui_grid.shape[2]

    evaluate.eval_spline_cube(spline._this, <double*>center.data,
                              <double*>output.data, ui_grid._this)

def eval_spline_grid(CubicSpline spline not None,
                     np.ndarray[double, ndim=1] center not None,
                     np.ndarray[double, ndim=1] output not None,
                     np.ndarray[double, ndim=2] points not None,
                     horton.cext.Cell cell not None):
    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3
    assert output.flags['C_CONTIGUOUS']
    assert points.flags['C_CONTIGUOUS']
    assert points.shape[1] == 3
    assert points.shape[0] == output.shape[0]

    evaluate.eval_spline_grid(spline._this, <double*>center.data,
                              <double*>output.data, <double*>points.data,
                              cell._this, output.shape[0])


#
# rtransform
#


cdef class RTransform(object):
    cdef rtransform.RTransform* _this

    property npoint:
        def __get__(self):
            return self._this.get_npoint()

    def radius(self, double t):
        return self._this.radius(t)

    def deriv(self, double t):
        return self._this.deriv(t)

    def inv(self, double r):
        return self._this.inv(r)

    def radius_array(self, np.ndarray[double, ndim=1] t not None,
                           np.ndarray[double, ndim=1] r not None):
        assert t.flags['C_CONTIGUOUS']
        cdef int n = t.shape[0]
        assert r.flags['C_CONTIGUOUS']
        assert r.shape[0] == n
        self._this.radius_array(<double*>t.data, <double*>r.data, n)

    def deriv_array(self, np.ndarray[double, ndim=1] t not None,
                          np.ndarray[double, ndim=1] d not None):
        assert t.flags['C_CONTIGUOUS']
        cdef int n = t.shape[0]
        assert d.flags['C_CONTIGUOUS']
        assert d.shape[0] == n
        self._this.deriv_array(<double*>t.data, <double*>d.data, n)

    def inv_array(self, np.ndarray[double, ndim=1] r not None,
                        np.ndarray[double, ndim=1] t not None):
        assert r.flags['C_CONTIGUOUS']
        cdef int n = r.shape[0]
        assert t.flags['C_CONTIGUOUS']
        assert t.shape[0] == n
        self._this.inv_array(<double*>r.data, <double*>t.data, n)

    def get_radii(self):
        '''Return an array with radii'''
        result = np.arange(self.npoint, dtype=float)
        self.radius_array(result, result)
        return result

    def get_volume_elements(self):
        '''Return an array with volume elements associated with the transform'''
        result = np.arange(self.npoint, dtype=float)
        self.deriv_array(result, result)
        return result

    @classmethod
    def from_string(cls, s):
        '''Construct a RTransform subclass from a string.'''
        words = s.split()
        clsname = words[0]
        args = words[1:]
        if clsname == 'IdentityRTransform':
            if len(args) != 1:
                raise ValueError('The IdentityRTransform needs one argument, got %i.' % len(words))
            npoint = int(args[0])
            return IdentityRTransform(npoint)
        if clsname == 'LinearRTransform':
            if len(args) != 3:
                raise ValueError('The LinearRTransform needs three arguments, got %i.' % len(words))
            rmin = float(args[0])
            rmax = float(args[1])
            npoint = int(args[2])
            return LinearRTransform(rmin, rmax, npoint)
        if clsname == 'ExpRTransform':
            if len(args) != 3:
                raise ValueError('The ExpRTransform needs three arguments, got %i.' % len(words))
            rmin = float(args[0])
            rmax = float(args[1])
            npoint = int(args[2])
            return ExpRTransform(rmin, rmax, npoint)
        if clsname == 'ShiftedExpRTransform':
            if len(args) != 4:
                raise ValueError('The ShiftedExpRTransform needs four arguments, got %i.' % len(words))
            rmin = float(args[0])
            rshift = float(args[1])
            rmax = float(args[2])
            npoint = int(args[3])
            return ShiftedExpRTransform(rmin, rshift, rmax, npoint)
        if clsname == 'BakerRTransform':
            if len(args) != 2:
                raise ValueError('The BakerRTransform needs two arguments, got %i.' % len(words))
            rmax = float(args[0])
            npoint = int(args[1])
            return BakerRTransform(rmax, npoint)
        else:
            raise TypeError('Unkown RTransform subclass: %s' % clsname)

    def to_string(self):
        raise NotImplementedError

    def chop(self, npoint):
        raise NotImplementedError


cdef class IdentityRTransform(RTransform):
    '''For testing only'''
    def __cinit__(self, int npoint):
        self._this = <rtransform.RTransform*>(new rtransform.IdentityRTransform(npoint))

    def to_string(self):
        return ' '.join(['IdentityRTransform', repr(self.npoint)])

    def chop(self, npoint):
        return IdentityRTransform(npoint)


cdef class LinearRTransform(RTransform):
    '''A linear grid.

       The grid points are distributed as follows:

       .. math:: r_i = \\alpha i + r_0

       with

       .. math:: \\alpha = (r_{N-1} -r_0)/(N-1).
    '''
    def __cinit__(self, double rmin, double rmax, int npoint):
        self._this = <rtransform.RTransform*>(new rtransform.LinearRTransform(rmin, rmax, npoint))

    property rmin:
        def __get__(self):
            return (<rtransform.LinearRTransform*>self._this).get_rmin()

    property rmax:
        def __get__(self):
            return (<rtransform.LinearRTransform*>self._this).get_rmax()

    property alpha:
        def __get__(self):
            return (<rtransform.LinearRTransform*>self._this).get_alpha()

    def to_string(self):
        return ' '.join(['LinearRTransform', repr(self.rmin), repr(self.rmax), repr(self.npoint)])

    def chop(self, npoint):
        rmax = self.radius(npoint-1)
        return LinearRTransform(self.rmin, rmax, npoint)


cdef class ExpRTransform(RTransform):
    '''An exponential grid.

       The grid points are distributed as follows:

       .. math:: r_i = r_0 \\alpha^i

       with

       .. math:: \\alpha = \log(r_{N-1}/r_0)/(N-1).
    '''
    def __cinit__(self, double rmin, double rmax, int npoint):
        self._this = <rtransform.RTransform*>(new rtransform.ExpRTransform(rmin, rmax, npoint))

    property rmin:
        def __get__(self):
            return (<rtransform.ExpRTransform*>self._this).get_rmin()

    property rmax:
        def __get__(self):
            return (<rtransform.ExpRTransform*>self._this).get_rmax()

    property alpha:
        def __get__(self):
            return (<rtransform.ExpRTransform*>self._this).get_alpha()

    def to_string(self):
        return ' '.join(['ExpRTransform', repr(self.rmin), repr(self.rmax), repr(self.npoint)])

    def chop(self, npoint):
        rmax = self.radius(npoint-1)
        return ExpRTransform(self.rmin, rmax, npoint)


cdef class ShiftedExpRTransform(RTransform):
    r'''A shifted exponential grid.

       The grid points are distributed as follows:

       .. math:: r_i = r_0 \alpha^i - r_s

       with

       .. math::
            r_0 = r_m + r_s

       .. math::
            \alpha = \log\left(\frac{r_M+r_s}{r_0}\right)/(N-1).
    '''
    def __cinit__(self, double rmin, double rshift, double rmax, int npoint):
        self._this = <rtransform.RTransform*>(new rtransform.ShiftedExpRTransform(rmin, rshift, rmax, npoint))

    property rmin:
        def __get__(self):
            return (<rtransform.ShiftedExpRTransform*>self._this).get_rmin()

    property rshift:
        def __get__(self):
            return (<rtransform.ShiftedExpRTransform*>self._this).get_rshift()

    property rmax:
        def __get__(self):
            return (<rtransform.ShiftedExpRTransform*>self._this).get_rmax()

    property r0:
        def __get__(self):
            return (<rtransform.ShiftedExpRTransform*>self._this).get_r0()

    property alpha:
        def __get__(self):
            return (<rtransform.ShiftedExpRTransform*>self._this).get_alpha()

    def to_string(self):
        return ' '.join(['ShiftedExpRTransform', repr(self.rmin), repr(self.rshift), repr(self.rmax), repr(self.npoint)])

    def chop(self, npoint):
        rmax = self.radius(npoint-1)
        return ShiftedExpRTransform(self.rmin, self.rshift, rmax, npoint)


cdef class BakerRTransform(RTransform):
    r'''A grid introduced by Baker et al.

       The grid points are distributed as follows:

       .. math:: r_i = A*ln\left[1-\left(\frac{i}{npoint}\right)^2\right]

       with

       .. math:: A = \frac{1}{ln\left[1-\left(\frac{npoint-1}{npoint}\right)^2\right]}.
    '''
    def __cinit__(self, double rmax, int npoint):
        self._this = <rtransform.RTransform*>(new rtransform.BakerRTransform(rmax, npoint))

    def __init__(self, double rmax, int npoint):
        log.cite('baker1994', 'using the radial integration grids introduced by Baker et al')

    property rmax:
        def __get__(self):
            return (<rtransform.BakerRTransform*>self._this).get_rmax()

    property scale:
        def __get__(self):
            return (<rtransform.BakerRTransform*>self._this).get_scale()

    def to_string(self):
        return ' '.join(['BakerRTransform', repr(self.rmax), repr(self.npoint)])

    def chop(self, npoint):
        # This just can't work. :(
        raise NotImplementedError


#
# uniform
#


cdef class UniformIntGrid(object):
    def __cinit__(self, np.ndarray[double, ndim=1] origin not None,
                  np.ndarray[double, ndim=2] grid_rvecs not None,
                  np.ndarray[long, ndim=1] shape not None,
                  np.ndarray[long, ndim=1] pbc not None):
        assert origin.flags['C_CONTIGUOUS']
        assert origin.shape[0] == 3
        assert grid_rvecs.flags['C_CONTIGUOUS']
        assert grid_rvecs.shape[0] == 3
        assert grid_rvecs.shape[1] == 3
        assert shape.flags['C_CONTIGUOUS']
        assert shape.shape[0] == 3
        assert pbc.flags['C_CONTIGUOUS']
        assert pbc.shape[0] == 3

        self._grid_cell = horton.cext.Cell(grid_rvecs)
        rvecs = grid_rvecs*shape.reshape(-1,1)
        self._cell = horton.cext.Cell(rvecs[pbc.astype(bool)])
        self._this = <uniform.UniformIntGrid*>(new uniform.UniformIntGrid(
            <double*>origin.data,
            self._grid_cell._this,
            <long*>shape.data,
            <long*>pbc.data,
            self._cell._this,
        ))

    def __dealloc__(self):
        del self._this

    property origin:
        def __get__(self):
            cdef np.ndarray[double, ndim=1] result = np.empty(3, float)
            self._this.copy_origin(<double*>result.data)
            return result

    property grid_cell:
        def __get__(self):
            return self._grid_cell

    property shape:
        def __get__(self):
            cdef np.ndarray[long, ndim=1] result = np.empty(3, int)
            self._this.copy_shape(<long*>result.data)
            return result

    property size:
        def __get__(self):
            return np.product(self.shape)

    property pbc:
        def __get__(self):
            cdef np.ndarray[long, ndim=1] result = np.empty(3, int)
            self._this.copy_pbc(<long*>result.data)
            return result

    property cell:
        def __get__(self):
            return self._cell

    @classmethod
    def from_hdf5(cls, grp, lf):
        return cls(
            grp['origin'][:],
            grp['grid_rvecs'][:],
            grp['shape'][:],
            grp['pbc'][:],
        )

    def to_hdf5(self, grp):
        grp['grid_rvecs'] = self._grid_cell.rvecs
        grp['origin'] = self.origin
        grp['shape'] = self.shape
        grp['pbc'] = self.pbc

    def zeros(self):
        return np.zeros(self.shape, float)

    def eval_spline(self, CubicSpline spline not None,
                    np.ndarray[double, ndim=1] center not None,
                    np.ndarray[double, ndim=3] output not None):
        assert center.flags['C_CONTIGUOUS']
        assert center.shape[0] == 3
        assert output.flags['C_CONTIGUOUS']
        assert output.shape[0] == self.shape[0]
        assert output.shape[1] == self.shape[1]
        assert output.shape[2] == self.shape[2]

        evaluate.eval_spline_cube(spline._this, <double*>center.data, <double*>output.data, self._this)

    def integrate(self, *args):
        '''Integrate the product of all arguments

           **Arguments:**

           data1, data2, ...
                All arguments must be arrays with the same size as the number
                of grid points. The arrays contain the functions, evaluated
                at the grid points, that must be multiplied and integrated.

        '''
        # This is often convenient for cube grid data:
        args = [arg.ravel() for arg in args if arg is not None]
        # Similar to conventional integration routine:
        return dot_multi(*args)*self._grid_cell.volume

    def get_ranges_rcut(self, np.ndarray[double, ndim=1] center, double rcut):
        '''Return the ranges if indexes that lie within the cutoff sphere.

           **Arguments:**

           center
                The center of the cutoff sphere

           rcut
                The radius of the cutoff sphere

           The ranges are trimmed to avoid points that fall of non-periodic
           boundaries of the grid.
        '''
        assert center.flags['C_CONTIGUOUS']
        assert center.size == 3
        assert rcut >= 0

        cdef np.ndarray[long, ndim=1] ranges_begin = np.zeros(3, int)
        cdef np.ndarray[long, ndim=1] ranges_end = np.zeros(3, int)
        self._this.set_ranges_rcut(
            <double*>center.data, rcut, <long*> ranges_begin.data,
            <long*> ranges_end.data)
        return ranges_begin, ranges_end

    def dist_grid_point(self, np.ndarray[double, ndim=1] center, np.ndarray[long, ndim=1] indexes):
        '''Return the distance between a center and a grid point

           **Arguments:**

           center
                The center

           indexes
                The integer indexes of the grid point (may fall outside of shape)
        '''
        assert center.flags['C_CONTIGUOUS']
        assert center.size == 3
        assert indexes.flags['C_CONTIGUOUS']
        assert indexes.size == 3
        return self._this.dist_grid_point(<double*>center.data, <long*>indexes.data)

    def delta_grid_point(self, np.ndarray[double, ndim=1] center, np.ndarray[long, ndim=1] indexes):
        '''Return the vector **from** a center **to** a grid point

           **Arguments:**

           center
                The center

           indexes
                The integer indexes of the grid point (may fall outside of shape)
        '''
        assert center.flags['C_CONTIGUOUS']
        assert center.size == 3
        assert indexes.flags['C_CONTIGUOUS']
        assert indexes.size == 3
        cdef np.ndarray[double, ndim=1] result = center.copy()
        self._this.delta_grid_point(<double*>result.data, <long*>indexes.data)
        return result

    # TODO: move this to cpart
    def compute_weight_corrections(self, funcs, rcut_scale=0.9, rcut_max=2.0, rcond=0.1):
        '''Computes corrections to the integration weights.

           **Arguments:**

           funcs
                A collection of functions that must integrate exactly with the
                corrected weights. The format is as follows. ``funcs`` is a
                list with tuples that contain three items:

                * center: the center for a set of spherically symmetric
                  functions. In pracice, this will always coincide with th
                  position of a nucleus.

                * Radial functions specified as a list of splines.

           **Optional arguments:**

           rcut_scale
                For center (of a spherical function), radii of non-overlapping
                spheres are determined by setting the radius of each sphere at
                0.5*rcut_scale*(distance to nearest atom or periodic image).

           rcut_max
                To avoid gigantic cutoff spheres, one may use rcut_max to set
                the maximum radius of the cutoff sphere.

           rcond
                The regulatization strength for the weight correction equations.
                This should not be too low. Current value is a compromise
                between accuracy and transferability of the weight corrections.

           **Return value:**

           The return value is a data array that can be provided as an
           additional argument to the ``integrate`` method. This should
           improve the accuracy of the integration for data that is similar
           to a linear combination of the provided sphericall functions.
        '''
        from horton.grid.int1d import SimpsonIntegrator1D

        result = np.ones(self.shape, float)
        volume = self._grid_cell.volume

        # initialize cutoff radii
        if self._cell.nvec > 0:
            rcut_max = min(rcut_max, 0.5*rcut_scale*self._cell.rspacings.min())
        rcuts = np.zeros(len(funcs)) + rcut_max

        # determine safe cutoff radii
        for i0 in xrange(len(funcs)):
            center0, rcut0 = funcs[i0][:2]
            for i1 in xrange(i0):
                center1, rcut1 = funcs[i1][:2]
                delta = center1 - center0
                self._cell.mic(delta)
                dist = np.linalg.norm(delta)
                rcut = 0.5*rcut_scale*dist
                rcuts[i0] = min(rcut, rcuts[i0])
                rcuts[i1] = min(rcut, rcuts[i1])

        def get_aux_grid(center, aux_rcut):
            ranges_begin, ranges_end = self._grid_cell.get_ranges_rcut(self.origin-center, aux_rcut)
            aux_origin = self.origin.copy()
            self._grid_cell.add_rvec(aux_origin, ranges_begin)
            aux_shape = ranges_end - ranges_begin
            aux_grid = UniformIntGrid(aux_origin, self._grid_cell.rvecs, aux_shape, np.zeros(3, int))
            return aux_grid, -ranges_begin

        def get_tapered_spline(spline, rcut, aux_rcut):
            assert rcut < aux_rcut
            rtf = spline.rtransform
            r = rtf.get_radii()
            # Get original spline stuff
            y = spline.copy_y()
            d = spline.deriv(r)
            # adapt cutoffs to indexes of radial grid
            ibegin = r.searchsorted(rcut)
            iend = r.searchsorted(aux_rcut)-1
            rcut = r[ibegin]
            aux_rcut = r[iend]
            # define tapering function
            sy = np.zeros(len(r))
            sd = np.zeros(len(r))
            sy[:ibegin] = 1.0
            scale = np.pi/(aux_rcut-rcut)
            x = scale*(r[ibegin:iend+1]-rcut)
            sy[ibegin:iend+1] = 0.5*(np.cos(x)+1)
            sd[ibegin:iend+1] = -0.5*(np.sin(x))*scale
            # construct product
            ty = y*sy
            td = d*sy+y*sd
            # construct spline
            tapered_spline = CubicSpline(ty, td, rtf)
            # compute integral
            int1d = SimpsonIntegrator1D()
            int_exact = 4*np.pi*dot_multi(
                ty, r, r, int1d.get_weights(len(r)), rtf.get_volume_elements()
            )
            # done
            return tapered_spline, int_exact

        icenter = 0
        for (center, splines), rcut in zip(funcs, rcuts):
            # A) Determine the points inside the cutoff sphere.
            ranges_begin, ranges_end = self._grid_cell.get_ranges_rcut(self.origin-center, rcut)

            # B) Construct a set of grid indexes that lie inside the sphere.
            nselect_max = np.product(ranges_end-ranges_begin)
            indexes = np.zeros((nselect_max, 3), int)
            nselect = self._grid_cell.select_inside(self.origin, center, rcut, ranges_begin, ranges_end, self.shape, self.pbc, indexes)
            indexes = indexes[:nselect]

            # C) Set up an integration grid for the tapered spline
            aux_rcut = 2*rcut
            aux_grid, aux_offset = get_aux_grid(center, aux_rcut)
            aux_indexes = (indexes + aux_offset) % self.shape

            # D) Allocate the arrays for the least-squares fit of the
            # corrections.
            neq = len(splines)
            dm = np.zeros((neq+1, nselect), float)
            ev = np.zeros(neq+1, float)

            # E) Fill in the coefficients. This is the expensive part.
            ieq = 0
            tmp = np.zeros(aux_grid.shape)
            av = np.zeros(neq+1)
            for spline in splines:
                if log.do_medium:
                    log("Computing spherical function. icenter=%i ieq=%i" % (icenter, ieq))
                tapered_spline, int_exact = get_tapered_spline(spline, rcut, aux_rcut)
                tmp[:] = 0.0
                aux_grid.eval_spline(tapered_spline, center, tmp)
                int_approx = self.integrate(tmp)
                dm[ieq] = volume*tmp[aux_indexes[:,0], aux_indexes[:,1], aux_indexes[:,2]]
                av[ieq] = int_approx
                ev[ieq] = int_exact - int_approx
                ieq += 1

            # Add error on constant function
            dm[neq] = volume
            av[neq] = 0.0
            ev[neq] = 0.0

            # rescale equations to optimize condition number
            scales = np.sqrt((dm**2).mean(axis=1))
            dm /= scales.reshape(-1,1)
            ev /= scales
            av /= scales

            # E) Find a regularized least norm solution.
            U, S, Vt = np.linalg.svd(dm, full_matrices=False)
            ridge = rcond*S[0]
            Sinv = S/(ridge**2+S**2)
            corrections = np.dot(Vt.T, np.dot(U.T, ev)*Sinv)

            # constrain the solution to integrate constant function exactly
            HtVSinv = Vt.sum(axis=1)*Sinv
            mu = corrections.sum()/np.dot(HtVSinv,HtVSinv)
            corrections -= mu*np.dot(Vt.T, Vt.sum(axis=1)*Sinv**2)

            if log.do_medium:
                rmsd = np.sqrt((corrections**2).mean())
                log('icenter=%i NSELECT=%i CN=%.3e RMSD=%.3e' % (icenter, nselect, S[0]/S[-1], rmsd))
                mv = np.dot(dm, corrections)
                for ieq in xrange(neq):
                    log('   spline %3i    error %+.3e   orig %+.3e  exact %+.3e' % (ieq, ev[ieq]-mv[ieq], ev[ieq], ev[ieq]+av[ieq]))
                log('   constant      error %+.3e' % corrections.sum())

            # F) Fill the corrections into the right place:
            result[indexes[:,0], indexes[:,1], indexes[:,2]] += corrections

            icenter += 1

        return result

    def get_window(self, np.ndarray[double, ndim=1] center, double rcut):
        begin, end = self.get_ranges_rcut(center, rcut)
        return UniformIntGridWindow(self, begin, end)


cdef class UniformIntGridWindow(object):
    def __cinit__(self, UniformIntGrid ui_grid not None,
                  np.ndarray[long, ndim=1] begin not None,
                  np.ndarray[long, ndim=1] end not None):
        assert begin.flags['C_CONTIGUOUS']
        assert begin.shape[0] == 3
        assert end.flags['C_CONTIGUOUS']
        assert end.shape[0] == 3

        self._ui_grid = ui_grid
        self._this = new uniform.UniformIntGridWindow(
            ui_grid._this,
            <long*>begin.data,
            <long*>end.data,
        )

    def __dealloc__(self):
        del self._this

    property ui_grid:
        def __get__(self):
            return self._ui_grid

    property begin:
        def __get__(self):
            cdef np.ndarray[long, ndim=1] result = np.empty(3, int)
            self._this.copy_begin(<long*>result.data)
            return result

    property end:
        def __get__(self):
            cdef np.ndarray[long, ndim=1] result = np.empty(3, int)
            self._this.copy_end(<long*>result.data)
            return result

    property shape:
        def __get__(self):
            return self.end - self.begin

    def get_window_ui_grid(self):
        grid_cell = self._ui_grid.grid_cell
        origin = self._ui_grid.origin.copy()
        grid_cell.add_rvec(origin, self.begin)
        return UniformIntGrid(origin, grid_cell.rvecs, self.shape, np.zeros(3, int))

    def zeros(self):
        return np.zeros(self.shape, float)

    def extend(self, np.ndarray[double, ndim=3] small not None,
               np.ndarray[double, ndim=3] output not None):
        assert small.flags['C_CONTIGUOUS']
        shape = self._ui_grid.shape
        assert small.shape[0] == shape[0]
        assert small.shape[1] == shape[1]
        assert small.shape[2] == shape[2]
        assert output.flags['C_CONTIGUOUS']
        shape = self.shape
        assert output.shape[0] == shape[0]
        assert output.shape[1] == shape[1]
        assert output.shape[2] == shape[2]

        self._this.extend(<double*>small.data, <double*>output.data)

    def eval_spline(self, CubicSpline spline not None,
                    np.ndarray[double, ndim=1] center not None,
                    np.ndarray[double, ndim=3] output not None):
        assert center.flags['C_CONTIGUOUS']
        assert center.shape[0] == 3
        assert output.flags['C_CONTIGUOUS']
        assert output.shape[0] == self.shape[0]
        assert output.shape[1] == self.shape[1]
        assert output.shape[2] == self.shape[2]

        # construct an ui_grid for this window such that we can reuse an existing routine
        cdef UniformIntGrid window_ui_grid = self.get_window_ui_grid()
        evaluate.eval_spline_cube(spline._this, <double*>center.data, <double*>output.data, window_ui_grid._this)

    def integrate(self, *args, **kwargs):
        '''Integrate the product of all arguments

           **Arguments:**

           data1, data2, ...
                All arguments must be arrays with the same size as the number
                of grid points. The arrays contain the functions, evaluated
                at the grid points, that must be multiplied and integrated.

           **Optional arguments:**

           center
                When given, a multipole moment can be computed with respect to
                this center instead of a plain integral.

           nx, ny, nz, nr
                The powers that determine the type of moment computed. These can
                only be given if center is given.
        '''
        # process arguments:
        args = [arg.ravel() for arg in args if arg is not None]

        # process keyword arguments:
        center = kwargs.pop('center', None)
        grid_cell = self._ui_grid.grid_cell
        if center is None:
            # retgular integration
            if len(kwargs) > 0:
                raise TypeError('Unexpected keyword argument: %s' % kwargs.popitem()[0])

            # Similar to conventional integration routine:
            return dot_multi(*args)*grid_cell.volume
        else:
            # integration with some polynomial factor in the integrand
            nx = kwargs.pop('nx', 0)
            ny = kwargs.pop('ny', 0)
            nz = kwargs.pop('nz', 0)
            nr = kwargs.pop('nr', 0)
            if len(kwargs) > 0:
                raise TypeError('Unexpected keyword argument: %s' % kwargs.popitem()[0])
            assert center.flags['C_CONTIGUOUS']
            assert center.shape[0] == 3

            # advanced integration routine:
            window_ui_grid = self.get_window_ui_grid()
            return dot_multi_moments_cube(args, window_ui_grid, center, nx, ny, nz, nr)*grid_cell.volume

    def compute_weight_corrections(self, funcs, rcut_scale=0.9, rcut_max=2.0, rcond=0.1):
        window_ui_grid = self.get_window_ui_grid()
        return window_ui_grid.compute_weight_corrections(funcs, rcut_scale, rcut_max, rcond)


def index_wrap(long i, long high):
    return uniform.index_wrap(i, high)


cdef class Block3Iterator(object):
    '''Wrapper for testing only'''
    cdef uniform.Block3Iterator* _this
    cdef np.ndarray _begin
    cdef np.ndarray _end
    cdef np.ndarray _shape

    def __cinit__(self, np.ndarray[long, ndim=1] begin not None,
                  np.ndarray[long, ndim=1] end not None,
                  np.ndarray[long, ndim=1] shape not None):
        assert begin.flags['C_CONTIGUOUS']
        assert begin.shape[0] == 3
        assert end.flags['C_CONTIGUOUS']
        assert end.shape[0] == 3
        assert shape.flags['C_CONTIGUOUS']
        assert shape.shape[0] == 3

        self._begin = begin
        self._end = end
        self._shape = shape
        self._this = new uniform.Block3Iterator(
            <long*>begin.data,
            <long*>end.data,
            <long*>shape.data,
        )

    property block_begin:
        def __get__(self):
            cdef np.ndarray[long, ndim=1] result = np.zeros(3, int)
            self._this.copy_block_begin(<long*>result.data)
            return result

    property block_end:
        def __get__(self):
            cdef np.ndarray[long, ndim=1] result = np.zeros(3, int)
            self._this.copy_block_end(<long*>result.data)
            return result

#
# utils
#

# TODO: eliminate duplicate code in dot routines

cdef _check_integranda(integranda, npoint=None):
    for integrandum in integranda:
        assert integrandum.flags['C_CONTIGUOUS']
        if npoint is None:
            npoint = integrandum.shape[0]
        else:
            assert npoint == integrandum.shape[0]
    return npoint


def dot_multi(*integranda):
    if len(integranda) == 0:
        return 0.0

    npoint = _check_integranda(integranda)

    cdef double** pointers = <double **>malloc(len(integranda)*sizeof(double*))
    if pointers == NULL:
        raise MemoryError()
    cdef np.ndarray[double, ndim=1] integrandum
    for i in xrange(len(integranda)):
        integrandum = integranda[i]
        pointers[i] = <double*>integrandum.data

    result = utils.dot_multi(npoint, len(integranda), pointers)

    free(pointers)
    return result


def dot_multi_moments_cube(integranda, UniformIntGrid ui_grid, np.ndarray[double, ndim=1] center not None, long nx, long ny, long nz, long nr):
    npoint = _check_integranda(integranda, ui_grid.size)
    # Only non-periodic grids are supported to guarantee an unambiguous definition of the polynomial.
    assert ui_grid.pbc[0] == 0
    assert ui_grid.pbc[1] == 0
    assert ui_grid.pbc[2] == 0
    #
    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3
    assert nx >= 0
    assert ny >= 0
    assert nz >= 0
    assert nr >= 0

    cdef double** pointers = <double **>malloc(len(integranda)*sizeof(double*))
    if pointers == NULL:
        raise MemoryError()
    cdef np.ndarray[double, ndim=1] integrandum
    for i in xrange(len(integranda)):
        integrandum = integranda[i]
        pointers[i] = <double*>integrandum.data

    result = utils.dot_multi_moments_cube(len(integranda), pointers, ui_grid._this, <double*>center.data, nx, ny, nz, nr)

    free(pointers)
    return result


def dot_multi_moments(integranda,
                      np.ndarray[double, ndim=2] points not None,
                      np.ndarray[double, ndim=1] center not None,
                      long nx, long ny, long nz, long nr):
    assert points.flags['C_CONTIGUOUS']
    assert points.shape[1] == 3
    npoint = _check_integranda(integranda, points.shape[0])
    #
    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3
    assert nx >= 0
    assert ny >= 0
    assert nz >= 0
    assert nr >= 0

    cdef double** pointers = <double **>malloc(len(integranda)*sizeof(double*))
    if pointers == NULL:
        raise MemoryError()
    cdef np.ndarray[double, ndim=1] integrandum
    for i in xrange(len(integranda)):
        integrandum = integranda[i]
        pointers[i] = <double*>integrandum.data

    result = utils.dot_multi_moments(npoint, len(integranda), pointers, <double*>points.data, <double*>center.data, nx, ny, nz, nr)

    free(pointers)
    return result


def grid_distances(np.ndarray[double, ndim=2] points,
                   np.ndarray[double, ndim=1] center,
                   np.ndarray[double, ndim=1] distances):
    assert points.flags['C_CONTIGUOUS']
    npoint = points.shape[0]
    assert points.shape[1] == 3
    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3
    assert distances.flags['C_CONTIGUOUS']
    assert distances.shape[0] == npoint
    utils.grid_distances(<double*>points.data, <double*>center.data,
                         <double*>distances.data, npoint)
