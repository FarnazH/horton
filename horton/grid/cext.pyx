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
    # utils
    'dot_multi', 'grid_distances',
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

    property rtransform:
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
                     np.ndarray[double, ndim=1] origin,
                     horton.cext.Cell grid_cell,
                     np.ndarray[long, ndim=1] shape,
                     np.ndarray[long, ndim=1] pbc_active):

    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3
    assert shape.flags['C_CONTIGUOUS']
    assert shape.shape[0] == 3
    assert output.flags['C_CONTIGUOUS']
    assert output.shape[0] == shape[0]
    assert output.shape[1] == shape[1]
    assert output.shape[2] == shape[2]
    assert origin.flags['C_CONTIGUOUS']
    assert origin.shape[0] == 3
    assert pbc_active.flags['C_CONTIGUOUS']
    assert pbc_active.shape[0] == 3

    evaluate.eval_spline_cube(spline._this, <double*>center.data,
                              <double*>output.data, <double*>origin.data,
                              grid_cell._this, <long*>shape.data,
                              <long*>pbc_active.data,)

def eval_spline_grid(CubicSpline spline,
                     np.ndarray[double, ndim=1] center,
                     np.ndarray[double, ndim=1] output,
                     np.ndarray[double, ndim=2] points,
                     horton.cext.Cell cell):
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


cdef class IdentityRTransform(RTransform):
    '''For testing only'''
    def __cinit__(self, int npoint):
        self._this = <rtransform.RTransform*>(new rtransform.IdentityRTransform(npoint))

    def to_string(self):
        return ' '.join(['IdentityRTransform', repr(self.npoint)])


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


cdef class BakerRTransform(RTransform):
    r'''A grid introduced by Baker et al.

       The grid points are distributed as follows:

       .. math:: r_i = A*ln\left[1-\left(\frac{i}{npoint}\right)^2\right]

       with

       .. math:: A = \frac{1}{A*ln\left[1-\left(\frac{npoint-1}{npoint}\right)^2\right]}.
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


#
# utils
#


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
