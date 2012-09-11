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
'''Molecular integration grids'''



import numpy as np

from horton.grid.base import BaseGrid
from horton.grid.atgrid import AtomicGrid, get_atomic_grid_size
from horton.grid.cext import becke_helper_atom
from horton.periodic import periodic


__all__ = [
    'BeckeMolGrid'
]



class BeckeMolGrid(BaseGrid):
    '''Molecular integration grid using Becke weights'''
    def __init__(self, numbers, centers, atspecs, k=3, random_rotate=True):
        if len(numbers.shape) != 1 or numbers.dtype != int:
            raise TypeError('Numbers must be a 1D array of integers.')
        natom = len(numbers)
        if numbers.min() < 0 or numbers.max() > len(periodic.elements)-1:
            raise ValueError('Atomic numbers are out of range.')
        if len(centers.shape) != 2 or centers.shape[0] != natom or centers.shape[1] != 3:
            raise TypeError('The array of centers is not compatible with the array of atomic numbers.')

        # transform atspecs into usable format
        size, atspecs = get_mol_grid_size(atspecs, natom)

        # assign attributes
        self._numbers = numbers
        self._centers = centers
        self._atspecs = atspecs
        self._k = k
        self._random_rotate = random_rotate

        # allocate memory for the grid
        points = np.zeros((size, 3), float)
        weights = np.zeros(size, float)

        # construct the atomic grids
        atgrids = []
        offset = 0
        for i in xrange(len(numbers)):
            rtransform, atnlls, atsize = atspecs[i]
            atgrid = AtomicGrid(centers[i], rtransform, atnlls, atsize, random_rotate, points[offset:offset+atsize])
            atgrids.append(atgrid)
            offset += atsize

        # assign partitioning weights
        self._init_weights(atgrids, weights)

        # finish
        BaseGrid.__init__(self, points, weights, atgrids)

    def _init_weights(self, atgrids, weights):
        offset = 0
        radii = np.array([periodic[n].cov_radius for n in self._numbers])
        for i in xrange(len(atgrids)):
            atgrid = atgrids[i]
            atsize = atgrid.size
            atweights = weights[offset:offset+atsize]

            becke_helper_atom(atgrid.points, atweights, radii, self._centers, i, self._k)
            atweights[:] *= atgrid.weights

            offset += atsize

    def _get_numbers(self):
        '''The atomic numbers of the grid.'''
        return self._numbers

    numbers = property(_get_numbers)

    def _get_centers(self):
        '''The centers of the grid.'''
        return self._centers

    centers = property(_get_centers)

    def _get_atspecs(self):
        '''The specifications of the atomic grids.'''
        return self._atspecs

    atspecs = property(_get_atspecs)

    def _get_k(self):
        '''The order of the Becke polynamial.'''
        return self._k

    k = property(_get_k)

    def _get_random_rotate(self):
        '''The random rotation flag.'''
        return self._random_rotate

    random_rotate = property(_get_random_rotate)


def get_mol_grid_size(atspecs, ncenter):
    if not hasattr(atspecs, '__len__'):
        raise TypeError('atspecs must be iterable')
    else:
        if len(atspecs) == 0:
            raise TypeError('atspecs must have at least one item.')
        if not hasattr(atspecs[0], '__len__'):
            atspecs = [atspecs]*ncenter
        else:
            if not len(atspecs) == ncenter:
                raise TypeError('When a atspec is given per atom, the size of the list must match the number of atoms.')

    size = 0
    for i in xrange(len(atspecs)):
        atspec = atspecs[i]
        if len(atspec) == 3:
            nll, nsphere, rtransform = atspec
            nlls = [nll]*nsphere
        elif len(atspec) == 2:
            nlls, rtransform = atspec
        else:
            raise TypeError('An atomic grid spec must contain two or three elements')
        atsize = get_atomic_grid_size(nlls)[0]
        atspecs[i] = rtransform, nlls, atsize
        size += atsize

    return size, atspecs
