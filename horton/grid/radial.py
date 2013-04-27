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

from horton.grid.base import IntGrid
from horton.grid.cext import dot_multi
from horton.grid.int1d import SimpsonIntegrator1D


class RadialIntGrid(object):
    '''An integration grid for the radial component of a spherical coordinate system'''

    def __init__(self, rtransform, int1d=None):
        self._rtransform = rtransform
        if int1d is None:
            self._int1d = SimpsonIntegrator1D()
        else:
            self._int1d = int1d
        self._weights = (4*np.pi)*(
            self._rtransform.get_volume_elements()*
            self._rtransform.get_radii()**2*
            self._int1d.get_weights(rtransform.npoint)
        )

    def _get_size(self):
        '''The size of the grid.'''
        return self._weights.size

    size = property(_get_size)

    def _get_shape(self):
        '''The shape of the grid.'''
        return self._weights.shape

    shape = property(_get_shape)

    def _get_rtransform(self):
        '''The RTransform object of the grid.'''
        return self._rtransform

    rtransform = property(_get_rtransform)

    def _get_int1d(self):
        '''The 1D radial integrator object of the grid.'''
        return self._int1d

    int1d = property(_get_int1d)

    def _get_weights(self):
        '''The grid weights.'''
        return self._weights

    weights = property(_get_weights)

    def _get_radii(self):
        '''The positions of the radial grid points.'''
        return self._rtransform.get_radii()

    radii = property(_get_radii)

    def zeros(self):
        return np.zeros(self.shape)

    def integrate(self, *args):
        '''Integrate the product of all arguments

           **Arguments:**

           data1, data2, ...
                All arguments must be arrays with the same size as the number
                of grid points. The arrays contain the functions, evaluated
                at the grid points, that must be multiplied and integrated.

        '''
        # TODO: eliminate duplicate code with similar routines in other integration grid
        # process arguments:
        args = [arg.ravel() for arg in args if arg is not None]
        args.append(self.weights)
        return dot_multi(*args)
