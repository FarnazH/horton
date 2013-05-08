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
'''The symmetry tools in Horton are just meant to provide optional additional
   information on top of a System instance.
'''


import numpy as np

from horton.cext import Cell
from horton.periodic import periodic


__all__ = ['SymmetryError', 'Symmetry']


class SymmetryError(Exception):
    pass


class Symmetry(object):
    '''An optional symmetry descriptor for Horton System objects'''
    def __init__(self, name, generators, fracs, numbers, cell, labels=None):
        '''
           **Arguments:**

           name
                Whatever name you want to give to this symmetry. This is
                converted to a string.

           generators
                A list of (3,4) matrices where the first three columns contain
                the linear transformation matrix and the last column is a
                translation vector. These transformations act on the fractional
                (or reduced) coordinates.

           fracs
                The fractional coordinates of a primitive cell/unit.

           numbers
                The corresponding element numbers of the primitive cell/unit

           cell
                A Cell object. Even for isolated systems a cell object must
                be provided with nvec=0.

           **Optional arguments:**

           labels
                A list of unique labels for each atom in the primitive unit.
                These are generated from the numbers array when not given.
        '''
        for generator in generators:
            if not (isinstance(generator, np.ndarray) and generator.shape == (3, 4)):
                raise TypeError('the list of generators may only contain 3x4 arrays.')
        if not (isinstance(fracs, np.ndarray) and fracs.ndim == 2 and fracs.shape[1] == 3):
            raise TypeError('fracs must be a numpy array with three columns.')
        if not (isinstance(numbers, np.ndarray) and numbers.ndim == 1):
            raise TypeError('numbers must be a numpy one-dimensional array.')
        if numbers.shape[0] != fracs.shape[0]:
            raise TypeError('numbers and fracs are not consistent in size.')
        if not isinstance(cell, Cell):
            raise TypeError('The cell object must be of the Cell class.')
        if labels is None:
            labels = []
            for i, n in enumerate(numbers):
                labels.append('%s%i' % (periodic[n].symbol, i))
        else:
            if len(labels) != numbers.shape[0]:
                raise TypeError('The length of the labels list is not consistent with the number of atoms in the primitive unit.')
            if len(set(labels)) < len(labels):
                raise ValueError('Not all labels are unique.')

        self._name = str(name)
        self._generators = generators
        self._fracs = fracs
        self._numbers = numbers
        self._cell = cell
        self._labels = labels

    def _get_name(self):
        return self._name

    name = property(_get_name)

    def _get_generators(self):
        return self._generators

    generators = property(_get_generators)

    def _get_fracs(self):
        return self._fracs

    fracs = property(_get_fracs)

    def _get_numbers(self):
        return self._numbers

    numbers = property(_get_numbers)

    def _get_cell(self):
        return self._cell

    cell = property(_get_cell)

    def _get_labels(self):
        return self._labels

    labels = property(_get_labels)

    def generate(self):
        '''Returns a system object

           The following three values are returned

           coordinates
                Cartesian coordinates for all atoms.

           numbers
                Element numbers for all atoms.

           links
                An array of indexes to connect each atom back with an atom in
                the primitive cell.
        '''
        raise NotImplementedError

    def identity(self, system, threshold=0.1):
        '''Connect atoms in the primitive unit with atoms in the system object

           **Arguments:**

           system
                A system object where to atoms (with some minor deviation)
                adhere to this symmetry.

           **Optional arguments:**

           threshold
                The maximum allowed distance between the ideal atom position
                and the actual atom position

           **Returns:**

           links
                An array of indexes to connect each atom back with an atom in
                the primitive cell.

           If an atom in the System object can not be linked with an atom in
           the primitive unit, a SymmetryError is raised.
        '''
        raise NotImplementedError
