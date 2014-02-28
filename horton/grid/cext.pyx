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
'''C++ extensions'''


import numpy as np
from horton.log import log
from horton.grid.utils import parse_args_integrate
import numbers


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
    'Extrapolation', 'ZeroExtrapolation', 'CuspExtrapolation',
    'PowerExtrapolation', 'tridiagsym_solve', 'CubicSpline',
    'compute_cubic_spline_int_weights',
    # evaluate
    'index_wrap', 'eval_spline_cube', 'eval_spline_grid',
    # rtransform
    'RTransform', 'IdentityRTransform', 'LinearRTransform', 'ExpRTransform',
    'ShiftedExpRTransform', 'PowerRTransform',
    # UniformGrid
    'UniformGrid', 'UniformGridWindow', 'index_wrap', 'Block3Iterator',
    # utils
    'dot_multi', 'dot_multi_moments_cube', 'dot_multi_moments',
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


def lebedev_laikov_sphere(np.ndarray[double, ndim=2] points not None,
                          np.ndarray[double, ndim=1] weights not None):
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


def becke_helper_atom(np.ndarray[double, ndim=2] points not None,
                      np.ndarray[double, ndim=1] weights not None,
                      np.ndarray[double, ndim=1] radii not None,
                      np.ndarray[double, ndim=2] centers not None,
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

def tridiagsym_solve(np.ndarray[double, ndim=1] diag_mid not None,
                     np.ndarray[double, ndim=1] diag_up not None,
                     np.ndarray[double, ndim=1] right not None,
                     np.ndarray[double, ndim=1] solution not None):
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


cdef class Extrapolation(object):
    cdef cubic_spline.Extrapolation* _this

    def __dealloc__(self):
        del self._this

    def eval_left(self, double x):
        '''Evaluate the extrapolation function at the left of the cubic spline interval'''
        return self._this.eval_left(x)

    def eval_right(self, double x):
        '''Evaluate the extrapolation function at the right of the cubic spline interval'''
        return self._this.eval_right(x)

    def deriv_left(self, double x):
        '''Evaluate the extrapolation function derivative at the left of the cubic spline interval'''
        return self._this.deriv_left(x)

    def deriv_right(self, double x):
        '''Evaluate the extrapolation function derivative at the right of the cubic spline interval'''
        return self._this.deriv_right(x)

    def to_string(self):
        '''Return an extrapolation object in string respresentation'''
        return self.__class__.__name__

    @classmethod
    def from_string(cls, s):
        '''Create an extrpolation object from a string description'''
        words = s.split()
        if words[0] == 'ZeroExtrapolation':
            if len(words) != 1:
                raise ValueError('ZeroExtrapolation takes not arguments.')
            return ZeroExtrapolation()
        elif words[0] == 'CuspExtrapolation':
            if len(words) != 1:
                raise ValueError('CuspExtrapolation takes not arguments.')
            return CuspExtrapolation()
        elif words[0] == 'PowerExtrapolation':
            if len(words) != 2:
                raise ValueError('PowerExtrapolation takes one argument.')
            power = float(words[1])
            return PowerExtrapolation(power)
        else:
            raise NotImplementedError


cdef class ZeroExtrapolation(Extrapolation):
    '''Zero left and right of the cubic spline interval'''
    def __cinit__(self):
        self._this = <cubic_spline.Extrapolation*>(new cubic_spline.ZeroExtrapolation())


cdef class CuspExtrapolation(Extrapolation):
    '''Exponential extrapolation at the left side, zero at the right size'''
    def __cinit__(self):
        self._this = <cubic_spline.Extrapolation*>(new cubic_spline.CuspExtrapolation())


cdef class PowerExtrapolation(Extrapolation):
    '''Zero at the right side, power law at the left side'''
    def __cinit__(self, double power):
        self._this = <cubic_spline.Extrapolation*>(new cubic_spline.PowerExtrapolation(power))

    property power:
        '''The power parameters'''
        def __get__(self):
            return (<cubic_spline.PowerExtrapolation*>self._this).get_power()

    def to_string(self):
        return 'PowerExtrapolation %s' % repr(self.power)


cdef class CubicSpline(object):
    '''A cubic spline object

       **Arguments:**

       y
            The function values at the 1D grid.

       **Optional arguments:**

       dx
            The derivative of the function values at the 1D grid. If not given,
            they are determined such that the second derivative of the cubic
            spline is continuous at the grid points.

       rtransform
            The transformation object that specifies the 1D grid. If not given,
            an identity transform is used

       extrapolation
            The extrapolation object that specifies the spline function outside
            the interval determined by the 1D grid. By default,
            CuspExtrapolation() is used.
    '''
    cdef cubic_spline.CubicSpline* _this
    cdef Extrapolation _extrapolation
    cdef RTransform _rtransform
    cdef np.ndarray _y
    cdef np.ndarray _dx
    cdef np.ndarray _dt

    def __cinit__(self,
                  np.ndarray[double, ndim=1] y not None,
                  np.ndarray[double, ndim=1] dx=None,
                  RTransform rtransform=None,
                  Extrapolation extrapolation=None):
        assert y.flags['C_CONTIGUOUS']
        self._y = y
        n = y.shape[0]

        # Set the rtransform
        if rtransform is None:
            self._rtransform = IdentityRTransform(n)
        else:
            self._rtransform = rtransform
            assert rtransform.npoint == n

        # use given derivatives or construct new ones.
        v = self._rtransform.get_deriv()
        if dx is None:
            self._dt = np.zeros(n, float)
            cubic_spline.solve_cubic_spline_system(<double*>y.data, <double*>self._dt.data, n)
            self._dx = self._dt/v
        else:
            assert dx.flags['C_CONTIGUOUS']
            assert dx.shape[0] == n
            self._dx = dx
            self._dt = dx*v

        # Only exponential extrapolation is needed for now
        if extrapolation is None:
            self._extrapolation = CuspExtrapolation()
        else:
            self._extrapolation = extrapolation

        self._this = new cubic_spline.CubicSpline(
            <double*>self._y.data, <double*>self._dt.data, self._extrapolation._this,
            self._rtransform._this, n
        )

    def __dealloc__(self):
        del self._this

    @classmethod
    def from_hdf5(cls, grp, lf):
        return cls(
            grp['y'][:],
            grp['d'][:],
            RTransform.from_string(grp.attrs['rtransform']),
            Extrapolation.from_string(grp.attrs['extrapolation']),
        )

    def to_hdf5(self, grp):
        grp['y'] = self.y
        grp['d'] = self.dx
        grp.attrs['rtransform'] = self.rtransform.to_string()
        grp.attrs['extrapolation'] = self.extrapolation.to_string()

    property rtransform:
        '''The RTransform object used for this spline'''
        def __get__(self):
            return self._rtransform

    property extrapolation:
        '''The extrapolation object used for this spline'''
        def __get__(self):
            return self._extrapolation

    property y:
        '''Array with function values at the grid points'''
        def __get__(self):
            return self._y.view()

    property dx:
        '''Array with derivatives (towards x) at the grid points'''
        def __get__(self):
            return self._dx.view()

    property dt:
        '''Array with derivatives (towards t) at the grid points'''
        def __get__(self):
            return self._dt.view()

    def __call__(self, np.ndarray[double, ndim=1] new_x not None,
                 np.ndarray[double, ndim=1] new_y=None):
        '''evaluate the spline on a grid

           **Arguments:**

           new_x
                A numpy array with the x-values at which the spline must be
                evaluated.

           **Optional arguments:**

           new_y
                When given, it is used as output argument. This array must have
                the same size of new_x.

           **Returns:** new_y
        '''
        assert new_x.flags['C_CONTIGUOUS']
        new_n = new_x.shape[0]
        if new_y is None:
            new_y = np.zeros(new_n, float)
        else:
            assert new_y.flags['C_CONTIGUOUS']
            assert new_y.shape[0] == new_n
        self._this.eval(<double*>new_x.data, <double*>new_y.data, new_n)
        return new_y

    def deriv(self, np.ndarray[double, ndim=1] new_x not None,
              np.ndarray[double, ndim=1] new_dx=None):
        '''Evaluate the derivative of the spline (towards x) on a grid

           **Arguments:**

           new_x
                A numpy array with the x-values at which the spline must be
                evaluated.

           **Optional arguments:**

           new_dx
                When given, it is used as output argument. This array must have
                the same size of new_x.

           **Returns:** new_dx
        '''
        assert new_x.flags['C_CONTIGUOUS']
        new_n = new_x.shape[0]
        if new_dx is None:
            new_dx = np.zeros(new_n, float)
        else:
            assert new_dx.flags['C_CONTIGUOUS']
            assert new_dx.shape[0] == new_n
        self._this.eval_deriv(<double*>new_x.data, <double*>new_dx.data, new_n)
        return new_dx


def compute_cubic_spline_int_weights(np.ndarray[double, ndim=1] weights not None):
    assert weights.flags['C_CONTIGUOUS']
    npoint = weights.shape[0]
    cubic_spline.compute_cubic_spline_int_weights(<double*>weights.data, npoint)


#
# evaluate
#


def index_wrap(long i, long high):
    return evaluate.index_wrap(i, high)


def eval_spline_cube(CubicSpline spline not None,
                     np.ndarray[double, ndim=1] center not None,
                     np.ndarray[double, ndim=3] output not None,
                     UniformGrid ugrid not None):
    '''Evaluate a spherically symmetric function on a uniform grid

       **Arguments:**

       spline
            The cubic spline that contains the radial dependence of the
            spherically symmetric function.

       center
            The center of the spherically symmetric function.

       output
            The output array in which the result is stored.

       ugrid
            An instance of UniformGrid that specifies the grid points.

       Note that, in case of periodic boundary conditions in the ugrid object,
       and when the spline as a non-zero tail, this routine may give
       inaccurate/incorrect results.
    '''
    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3
    assert output.flags['C_CONTIGUOUS']
    assert output.shape[0] == ugrid.shape[0]
    assert output.shape[1] == ugrid.shape[1]
    assert output.shape[2] == ugrid.shape[2]

    evaluate.eval_spline_cube(spline._this, <double*>center.data,
                              <double*>output.data, ugrid._this)

def eval_spline_grid(CubicSpline spline not None,
                     np.ndarray[double, ndim=1] center not None,
                     np.ndarray[double, ndim=1] output not None,
                     np.ndarray[double, ndim=2] points not None,
                     horton.cext.Cell cell not None):
    '''Evaluate a spherically symmetric function on a general grid

       **Arguments:**

       spline
            The cubic spline that contains the radial dependence of the
            spherically symmetric function.

       center
            The center of the spherically symmetric function.

       points
            An array with grid points, with shape (N, 3)

       output
            The output array in which the result is stored.

       cell
            A specification of the periodic boundary conditions.
    '''
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


# The following class contains a lot of duplicate code because Cython can not do this (yet):
# ctypedef double (rtransform.RTransform::*fn_ptr)(double)
# ctypedef void (rtransform.RTransform::*fn_array_ptr)(double*, double*,int)

cdef class RTransform(object):
    '''A definition of (radial) grid points by means of a transformation.

       The definition starts from a uniform 1D grid with spacing 1 and starting
       point 0: 0, 1, 2, 3, ... npoint-1. These values are defined on the
       so-called t-axis. The transformation is a function r=f(t) that defines
       the actual grid points on the r-axis: f(0), f(1), f(2), ... f(npoint-1).
       Different implementation for the function f are available.
    '''
    cdef rtransform.RTransform* _this

    property npoint:
        def __get__(self):
            return self._this.get_npoint()

    def radius(self, t, output=None):
        '''Return the 1D grid points for the given index(es)

           **Arguments:**

           t
                A number or an array of numbers for the indexes. t may be
                fractional or integer.
        '''
        if isinstance(t, numbers.Number):
            assert output is None
            return self._this.radius(t)
        elif isinstance(t, np.ndarray):
            return self._radius_array(t.astype(float), output)
        else:
            raise NotImplementedError

    def _radius_array(self, np.ndarray[double, ndim=1] t not None,
                            np.ndarray[double, ndim=1] output=None):
        assert t.flags['C_CONTIGUOUS']
        cdef int n = t.shape[0]
        if output is None:
            output = np.zeros(n, float)
        else:
            assert output.flags['C_CONTIGUOUS']
            assert output.shape[0] == n
        self._this.radius_array(<double*>t.data, <double*>output.data, n)
        return output

    def deriv(self, t, output=None):
        '''Return the derivative of the transformation for the given index(es)

           **Arguments:**

           t
                A number or an array of numbers for the indexes. t may be
                fractional or integer.
        '''
        if isinstance(t, numbers.Number):
            assert output is None
            return self._this.deriv(t.astype(float))
        elif isinstance(t, np.ndarray):
            return self._deriv_array(t, output)
        else:
            raise NotImplementedError

    def _deriv_array(self, np.ndarray[double, ndim=1] t not None,
                            np.ndarray[double, ndim=1] output=None):
        assert t.flags['C_CONTIGUOUS']
        cdef int n = t.shape[0]
        if output is None:
            output = np.zeros(n, float)
        else:
            assert output.flags['C_CONTIGUOUS']
            assert output.shape[0] == n
        self._this.deriv_array(<double*>t.data, <double*>output.data, n)
        return output

    def deriv2(self, t, output=None):
        '''Return the second derivative of the transformation for the given index(es)

           **Arguments:**

           t
                A number or an array of numbers for the indexes. t may be
                fractional or integer.
        '''
        if isinstance(t, numbers.Number):
            assert output is None
            return self._this.deriv2(t.astype(float))
        elif isinstance(t, np.ndarray):
            return self._deriv2_array(t, output)
        else:
            raise NotImplementedError

    def _deriv2_array(self, np.ndarray[double, ndim=1] t not None,
                            np.ndarray[double, ndim=1] output=None):
        assert t.flags['C_CONTIGUOUS']
        cdef int n = t.shape[0]
        if output is None:
            output = np.zeros(n, float)
        else:
            assert output.flags['C_CONTIGUOUS']
            assert output.shape[0] == n
        self._this.deriv2_array(<double*>t.data, <double*>output.data, n)
        return output

    def deriv3(self, t, output=None):
        '''Return the third of the transformation for the given index(es)

           **Arguments:**

           t
                A number or an array of numbers for the indexes. t may be
                fractional or integer.
        '''
        if isinstance(t, numbers.Number):
            assert output is None
            return self._this.deriv3(t.astype(float))
        elif isinstance(t, np.ndarray):
            return self._deriv3_array(t, output)
        else:
            raise NotImplementedError

    def _deriv3_array(self, np.ndarray[double, ndim=1] t not None,
                            np.ndarray[double, ndim=1] output=None):
        assert t.flags['C_CONTIGUOUS']
        cdef int n = t.shape[0]
        if output is None:
            output = np.zeros(n, float)
        else:
            assert output.flags['C_CONTIGUOUS']
            assert output.shape[0] == n
        self._this.deriv3_array(<double*>t.data, <double*>output.data, n)
        return output

    def inv(self, r, output=None):
        '''Return the indexes for given radial grid points

           **Arguments:**

           r
                A number or an array of numbers for the radial grid points.
        '''
        if isinstance(r, numbers.Number):
            assert output is None
            return self._this.inv(r)
        elif isinstance(r, np.ndarray):
            return self._inv_array(r.astype(float), output)
        else:
            raise NotImplementedError

    def _inv_array(self, np.ndarray[double, ndim=1] r not None,
                         np.ndarray[double, ndim=1] output=None):
        assert r.flags['C_CONTIGUOUS']
        cdef int n = r.shape[0]
        if output is None:
            output = np.zeros(n, float)
        else:
            assert output.flags['C_CONTIGUOUS']
            assert output.shape[0] == n
        self._this.inv_array(<double*>r.data, <double*>output.data, n)
        return output

    def get_radii(self):
        '''Return an array with radii'''
        result = np.arange(self.npoint, dtype=float)
        self._radius_array(result, result)
        return result

    def get_deriv(self):
        '''Return an array with derivatives at the grid points'''
        result = np.arange(self.npoint, dtype=float)
        self._deriv_array(result, result)
        return result

    def get_deriv2(self):
        '''Return an array with second derivatives at the grid points'''
        result = np.arange(self.npoint, dtype=float)
        self._deriv2_array(result, result)
        return result

    def get_deriv3(self):
        '''Return an array with third derivatives at the grid points'''
        result = np.arange(self.npoint, dtype=float)
        self._deriv3_array(result, result)
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
        elif clsname == 'LinearRTransform':
            if len(args) != 3:
                raise ValueError('The LinearRTransform needs three arguments, got %i.' % len(words))
            rmin = float(args[0])
            rmax = float(args[1])
            npoint = int(args[2])
            return LinearRTransform(rmin, rmax, npoint)
        elif clsname == 'ExpRTransform':
            if len(args) != 3:
                raise ValueError('The ExpRTransform needs three arguments, got %i.' % len(words))
            rmin = float(args[0])
            rmax = float(args[1])
            npoint = int(args[2])
            return ExpRTransform(rmin, rmax, npoint)
        elif clsname == 'ShiftedExpRTransform':
            if len(args) != 4:
                raise ValueError('The ShiftedExpRTransform needs four arguments, got %i.' % len(words))
            rmin = float(args[0])
            rshift = float(args[1])
            rmax = float(args[2])
            npoint = int(args[3])
            return ShiftedExpRTransform(rmin, rshift, rmax, npoint)
        elif clsname == 'PowerRTransform':
            if len(args) != 3:
                raise ValueError('The PowerRTransform needs three arguments, got %i.' % len(words))
            rmin = float(args[0])
            rmax = float(args[1])
            npoint = int(args[2])
            return PowerRTransform(rmin, rmax, npoint)
        else:
            raise TypeError('Unkown RTransform subclass: %s' % clsname)

    def to_string(self):
        '''Represent the rtransform object as a string'''
        raise NotImplementedError

    def chop(self, npoint):
        '''Return an rtransform with ``npoint`` number of grid points

           The remaining grid points are such that they coincide with those from
           the old rtransform.
        '''
        raise NotImplementedError

    def half(self):
        '''Return an rtransform with half the number of grid points

           The returned rtransform is such that old(2t+1) = new(t).
        '''
        raise NotImplementedError

    def get_default_int1d(self):
        '''Return the recommended 1D integrator for this rtransform'''
        from horton.grid.int1d import SimpsonIntegrator1D
        return SimpsonIntegrator1D()



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

    def half(self):
        if self.npoint %2 != 0:
            raise ValueError('Half method can only be called on a rtransform with an even number of points.')
        rmin = self.radius(1)
        return LinearRTransform(rmin, self.rmax, self.npoint/2)


cdef class ExpRTransform(RTransform):
    r'''An exponential grid.

       The grid points are distributed as follows:

       .. math:: r_i = r_0 \exp(\alpha i)

       with

       .. math:: \alpha = \log(r_{N-1}/r_0)/(N-1).
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

    def half(self):
        if self.npoint %2 != 0:
            raise ValueError('Half method can only be called on a rtransform with an even number of points.')
        rmin = self.radius(1)
        return ExpRTransform(rmin, self.rmax, self.npoint/2)


cdef class ShiftedExpRTransform(RTransform):
    r'''A shifted exponential grid.

       The grid points are distributed as follows:

       .. math:: r_i = r_0 \alpha^i - r_s

       with

       .. math::
            r_0 = r_{N-1} + r_s

       .. math::
            \alpha = \log\left(\frac{r_{N-1}+r_s}{r_0}\right)/(N-1).
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


cdef class PowerRTransform(RTransform):
    r'''A power grid.

       The grid points are distributed as follows:

       .. math:: r_i = r_0 i^{\alpha}

       with

       .. math::
            \alpha = \frac{\ln r_{N-1} - \ln r_0}{\ln N-1}
    '''
    def __cinit__(self, double rmin, double rmax, int npoint):
        self._this = <rtransform.RTransform*>(new rtransform.PowerRTransform(rmin, rmax, npoint))

    property rmin:
        def __get__(self):
            return (<rtransform.PowerRTransform*>self._this).get_rmin()

    property rmax:
        def __get__(self):
            return (<rtransform.PowerRTransform*>self._this).get_rmax()

    property power:
        def __get__(self):
            return (<rtransform.PowerRTransform*>self._this).get_power()

    def to_string(self):
        return ' '.join(['PowerRTransform', repr(self.rmin), repr(self.rmax), repr(self.npoint)])

    def chop(self, npoint):
        rmax = self.radius(npoint-1)
        return PowerRTransform(self.rmin, rmax, npoint)

    def half(self):
        if self.npoint %2 != 0:
            raise ValueError('Half method can only be called on a rtransform with an even number of points.')
        rmin = self.radius(1)
        return PowerRTransform(rmin, self.rmax, self.npoint/2)

    def get_default_int1d(self):
        from horton.grid.int1d import StubIntegrator1D
        return StubIntegrator1D()


#
# uniform
#


cdef class UniformGrid(object):
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

        self._this = <uniform.UniformGrid*>(new uniform.UniformGrid(
            <double*>origin.data,
            <double*>grid_rvecs.data,
            <long*>shape.data,
            <long*>pbc.data,
        ))

    def __dealloc__(self):
        del self._this

    property origin:
        def __get__(self):
            cdef np.npy_intp dims[1]
            dims[0] = 3
            cdef np.ndarray result = np.PyArray_SimpleNewFromData(1, dims, np.NPY_DOUBLE, self._this.origin)
            np.set_array_base(result, self)
            return result

    property grid_rvecs:
        def __get__(self):
            cdef np.npy_intp dims[2]
            dims[0] = 3
            dims[1] = 3
            cdef np.ndarray result = np.PyArray_SimpleNewFromData(2, dims, np.NPY_DOUBLE, self._this.grid_rvecs)
            np.set_array_base(result, self)
            return result

    property shape:
        def __get__(self):
            cdef np.npy_intp dims[1]
            dims[0] = 3
            cdef np.ndarray result = np.PyArray_SimpleNewFromData(1, dims, np.NPY_LONG, self._this.shape)
            np.set_array_base(result, self)
            return result

    property pbc:
        def __get__(self):
            cdef np.npy_intp dims[1]
            dims[0] = 3
            cdef np.ndarray result = np.PyArray_SimpleNewFromData(1, dims, np.NPY_LONG, self._this.pbc)
            np.set_array_base(result, self)
            return result

    property size:
        def __get__(self):
            return np.product(self.shape)

    def get_cell(self):
        cdef horton.cext.Cell result = horton.cext.Cell.__new__(horton.cext.Cell, initvoid=True)
        result._this = self._this.get_cell()
        return result

    def get_grid_cell(self):
        cdef horton.cext.Cell result = horton.cext.Cell.__new__(horton.cext.Cell, initvoid=True)
        result._this = self._this.get_grid_cell()
        return result

    @classmethod
    def from_hdf5(cls, grp, lf):
        return cls(
            grp['origin'][:],
            grp['grid_rvecs'][:],
            grp['shape'][:],
            grp['pbc'][:],
        )

    def to_hdf5(self, grp):
        grp['grid_rvecs'] = self.grid_rvecs
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
        return dot_multi(*args)*abs(np.linalg.det(self.grid_rvecs))

    def get_ranges_rcut(self, np.ndarray[double, ndim=1] center not None, double rcut):
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

    def dist_grid_point(self, np.ndarray[double, ndim=1] center not None,
                        np.ndarray[long, ndim=1] indexes not None):
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

    def delta_grid_point(self, np.ndarray[double, ndim=1] center not None,
                         np.ndarray[long, ndim=1] indexes not None):
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
    def compute_weight_corrections(self, funcs, rcut_scale=0.9, rcut_max=2.0, rcond=0.1, output=None):
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

        if output is None:
            output = np.ones(self.shape, float)
        else:
            output[:] = 1.0
        cell = self.get_cell()
        grid_cell = self.get_grid_cell()
        volume = grid_cell.volume

        # initialize cutoff radii
        if cell.nvec > 0:
            rcut_max = min(rcut_max, 0.5*rcut_scale*cell.rspacings.min())
        rcuts = np.zeros(len(funcs)) + rcut_max

        # determine safe cutoff radii
        for i0 in xrange(len(funcs)):
            center0, rcut0 = funcs[i0][:2]
            for i1 in xrange(i0):
                center1, rcut1 = funcs[i1][:2]
                delta = center1 - center0
                cell.mic(delta)
                dist = np.linalg.norm(delta)
                rcut = 0.5*rcut_scale*dist
                rcuts[i0] = min(rcut, rcuts[i0])
                rcuts[i1] = min(rcut, rcuts[i1])

        def get_aux_grid(center, aux_rcut):
            ranges_begin, ranges_end = grid_cell.get_ranges_rcut(self.origin-center, aux_rcut)
            aux_origin = self.origin.copy()
            grid_cell.add_rvec(aux_origin, ranges_begin)
            aux_shape = ranges_end - ranges_begin
            aux_grid = UniformGrid(aux_origin, grid_cell.rvecs, aux_shape, np.zeros(3, int))
            return aux_grid, -ranges_begin

        def get_tapered_spline(spline, rcut, aux_rcut):
            assert rcut < aux_rcut
            rtf = spline.rtransform
            r = rtf.get_radii()
            # Get original spline stuff
            y = spline.y
            d = spline.dx
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
                ty, r, r, int1d.get_weights(len(r)), rtf.get_deriv()
            )
            # done
            return tapered_spline, int_exact

        icenter = 0
        for (center, splines), rcut in zip(funcs, rcuts):
            # A) Determine the points inside the cutoff sphere.
            ranges_begin, ranges_end = grid_cell.get_ranges_rcut(self.origin-center, rcut)

            # B) Construct a set of grid indexes that lie inside the sphere.
            nselect_max = np.product(ranges_end-ranges_begin)
            indexes = np.zeros((nselect_max, 3), int)
            nselect = grid_cell.select_inside(self.origin, center, rcut, ranges_begin, ranges_end, self.shape, self.pbc, indexes)
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
            output[indexes[:,0], indexes[:,1], indexes[:,2]] += corrections

            icenter += 1

        return output

    def get_window(self, np.ndarray[double, ndim=1] center not None, double rcut):
        begin, end = self.get_ranges_rcut(center, rcut)
        return UniformGridWindow(self, begin, end)


cdef class UniformGridWindow(object):
    def __cinit__(self, UniformGrid ugrid not None,
                  np.ndarray[long, ndim=1] begin not None,
                  np.ndarray[long, ndim=1] end not None):
        assert begin.flags['C_CONTIGUOUS']
        assert begin.shape[0] == 3
        assert end.flags['C_CONTIGUOUS']
        assert end.shape[0] == 3

        self._ugrid = ugrid
        self._this = new uniform.UniformGridWindow(
            ugrid._this,
            <long*>begin.data,
            <long*>end.data,
        )

    def __dealloc__(self):
        del self._this

    property ugrid:
        def __get__(self):
            return self._ugrid

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

    property size:
        def __get__(self):
            return np.product(self.shape)

    def get_window_ugrid(self):
        grid_rvecs = self._ugrid.grid_rvecs
        origin = self._ugrid.origin.copy() + np.dot(self.begin, grid_rvecs)
        return UniformGrid(origin, grid_rvecs, self.shape, np.zeros(3, int))

    def zeros(self):
        return np.zeros(self.shape, float)

    def extend(self, np.ndarray[double, ndim=3] cell not None,
               np.ndarray[double, ndim=3] local not None):
        '''Copy a periodic repetation of the cell function to the local grid'''
        assert cell.flags['C_CONTIGUOUS']
        shape = self._ugrid.shape
        assert cell.shape[0] == shape[0]
        assert cell.shape[1] == shape[1]
        assert cell.shape[2] == shape[2]
        assert local.flags['C_CONTIGUOUS']
        shape = self.shape
        assert local.shape[0] == shape[0]
        assert local.shape[1] == shape[1]
        assert local.shape[2] == shape[2]
        self._this.extend(<double*>cell.data, <double*>local.data)

    def wrap(self, np.ndarray[double, ndim=3] local not None,
                   np.ndarray[double, ndim=3] cell not None):
        '''Write the local function to the periodic array, wrapping around the edges'''
        assert local.flags['C_CONTIGUOUS']
        shape = self.shape
        assert local.shape[0] == shape[0]
        assert local.shape[1] == shape[1]
        assert local.shape[2] == shape[2]
        assert cell.flags['C_CONTIGUOUS']
        shape = self._ugrid.shape
        assert cell.shape[0] == shape[0]
        assert cell.shape[1] == shape[1]
        assert cell.shape[2] == shape[2]
        self._this.wrap(<double*>local.data, <double*>cell.data)

    def eval_spline(self, CubicSpline spline not None,
                    np.ndarray[double, ndim=1] center not None,
                    np.ndarray[double, ndim=3] output not None):
        assert center.flags['C_CONTIGUOUS']
        assert center.shape[0] == 3
        assert output.flags['C_CONTIGUOUS']
        assert output.shape[0] == self.shape[0]
        assert output.shape[1] == self.shape[1]
        assert output.shape[2] == self.shape[2]

        # construct an ugrid for this window such that we can reuse an existing routine
        cdef UniformGrid window_ugrid = self.get_window_ugrid()
        evaluate.eval_spline_cube(spline._this, <double*>center.data, <double*>output.data, window_ugrid._this)

    def integrate(self, *args, **kwargs):
        '''Integrate the product of all arguments

           **Arguments:**

           data1, data2, ...
                All arguments must be arrays with the same size as the number
                of grid points. The arrays contain the functions, evaluated
                at the grid points, that must be multiplied and integrated.

           **Optional arguments:**

           center=None
                When given, multipole moments are computed with respect to
                this center instead of a plain integral.

           lmax=0
                The maximum angular momentum to consider when computing multipole
                moments

           mtype=1
                The type of multipole moments: 1=``cartesian``, 2=``pure``,
                3=``radial``.
        '''
        args, multipole_args, segments = parse_args_integrate(*args, **kwargs)
        if segments is not None:
            raise TypeError('Unexpected argument: segments')

        volume = abs(np.linalg.det(self._ugrid.grid_rvecs))
        if multipole_args is None:
            # regular integration
            return dot_multi(*args)*volume
        else:
            # computation of multipole expansion of the integrand
            center, lmax, mtype = multipole_args
            window_ugrid = self.get_window_ugrid()
            return dot_multi_moments_cube(args, window_ugrid, center, lmax, mtype)*volume

    def compute_weight_corrections(self, funcs, rcut_scale=0.9, rcut_max=2.0, rcond=0.1, output=None):
        window_ugrid = self.get_window_ugrid()
        return window_ugrid.compute_weight_corrections(funcs, rcut_scale, rcut_max, rcond, output)


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


def _check_integranda(integranda, npoint=None):
    assert len(integranda) > 0
    for integrandum in integranda:
        assert integrandum.flags['C_CONTIGUOUS']
        if npoint is None:
            npoint = integrandum.shape[0]
        else:
            assert npoint == integrandum.shape[0]
    return npoint


cdef double** _parse_integranda(integranda):
    cdef double** result = <double **>malloc(len(integranda)*sizeof(double*))
    if result == NULL:
        raise MemoryError()
    cdef np.ndarray[double, ndim=1] integrandum
    for i in xrange(len(integranda)):
        integrandum = integranda[i]
        result[i] = <double*>integrandum.data
    return result


def _parse_segments(segments, npoint):
    if segments is None:
        segments = np.array([npoint])
    assert segments.flags['C_CONTIGUOUS']
    nsegment = segments.shape[0]
    return segments, nsegment


def dot_multi(*integranda, np.ndarray[long, ndim=1] segments=None):
    '''Multiply the arguments piecewise and sum up the products

       **Arguments:**

       data1, data2, ...
            Arrays of the same size, whose elements will be multiplied piecewise
            and then added.

       **Optional arguments:**

       segments
            An array with segment sizes (integer). If given, the summation is
            carried out in segments of the given sizes and the return value is
            an array with the same size as segments.
    '''
    cdef long npoint = _check_integranda(integranda)
    segments, nsegment = _parse_segments(segments, npoint)
    cdef np.ndarray output = np.zeros(nsegment)
    cdef double** pointers = _parse_integranda(integranda)
    try:
        utils.dot_multi(npoint, len(integranda), pointers, <long*>segments.data, <double*>output.data)
    finally:
        free(pointers)
    if nsegment == 1:
        return output[0]
    else:
        return output


cdef long _get_nmoment(long lmax, long mtype):
    if mtype==1:
        # cartesian moments
        return ((lmax+1)*(lmax+2)*(lmax+3))/6
    elif mtype==2:
        # pure moments
        return (lmax+1)**2
    elif mtype==3:
        # radial moments
        return lmax+1
    else:
        raise ValueError('Unsupported mtype.')



def dot_multi_moments_cube(integranda, UniformGrid ugrid not None,
                           np.ndarray[double, ndim=1] center not None,
                           long lmax, long mtype):
    '''Multiply the arguments piecewise, including one of a series of multipole functions at a time, and sum up the products.

       **Arguments:**

       data1, data2, ...
            Arrays of the same size, whose elements will be multiplied piecewise
            and then added.

       center
            The origin for the multipole functions

       lmax
            The maximum angular momentum for the moments

       mtype
            The type of moments: 1=``cartesian``, 2=``pure``,
            3=``radial``, 4=``surface``.

       **Returns:** an array where the number of elements matches the number of
       multipole moments for the given combiantion of lmax and mtype.
    '''


    cdef long npoint = _check_integranda(integranda, ugrid.size)
    # Only non-periodic grids are supported to guarantee an unambiguous definition of the polynomial.
    assert ugrid.pbc[0] == 0
    assert ugrid.pbc[1] == 0
    assert ugrid.pbc[2] == 0
    #
    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3

    cdef long nmoment = _get_nmoment(lmax, mtype)
    cdef np.ndarray output = np.zeros(nmoment)
    cdef double** pointers = _parse_integranda(integranda)
    try:
        utils.dot_multi_moments_cube(len(integranda), pointers, ugrid._this, <double*>center.data, lmax, mtype, <double*>output.data, nmoment)
    finally:
        free(pointers)
    return output


def dot_multi_moments(integranda,
                      np.ndarray[double, ndim=2] points not None,
                      np.ndarray[double, ndim=1] center not None,
                      long lmax, long mtype,
                      np.ndarray[long, ndim=1] segments):
    '''Multiply the arguments piecewise, including one of a series of multipole functions at a time, and sum up the products.

       **Arguments:**

       data1, data2, ...
            Arrays of the same size, whose elements will be multiplied piecewise
            and then added.

       center
            The origin for the multipole functions

       lmax
            The maximum angular momentum for the moments

       mtype
            The type of moments: 1=``cartesian``, 2=``pure``,
            3=``radial``, 4=``surface``.

       segments
            An array with segment sizes (integer). If given, the summation is
            carried out in segments of the given sizes.

       **Returns:** an array where the number of elements matches the number of
       multipole moments for the given combiantion of lmax and mtype. If
       ``segments`` is given, the return array has two indices, the first one
       running over the segments and the second one running over the moments.
    '''

    assert points.flags['C_CONTIGUOUS']
    assert points.shape[1] == 3
    cdef long npoint = _check_integranda(integranda, points.shape[0])
    #
    assert center.flags['C_CONTIGUOUS']
    assert center.shape[0] == 3

    cdef long nmoment = _get_nmoment(lmax, mtype)
    segments, nsegment = _parse_segments(segments, npoint)
    cdef np.ndarray output = np.zeros((nsegment, nmoment))
    cdef double** pointers = _parse_integranda(integranda)
    try:
        utils.dot_multi_moments(npoint, len(integranda), pointers,
            <double*>points.data, <double*>center.data, lmax, mtype,
            <long*>segments.data, <double*>output.data, nmoment)
    finally:
        free(pointers)
    if nsegment == 1:
        return output[0]
    else:
        return output
