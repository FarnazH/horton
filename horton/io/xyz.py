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
'''XYZ File Format'''


import numpy as np

from horton.units import angstrom
from horton.periodic import periodic
from horton.io.common import typecheck_dump


__all__ = ['load_xyz', 'dump_xyz']


def load_xyz(filename):
    '''Load a molecular geometry from a .xyz file.

       **Argument:**

       filename
            The file to load the geometry from

       **Returns:** dictionary with coordinates and numbers.
    '''
    f = file(filename)
    size = int(f.next())
    f.next()
    coordinates = np.empty((size, 3), float)
    numbers = np.empty(size, int)
    for i in xrange(size):
        words = f.next().split()
        numbers[i] = periodic[words[0]].number
        coordinates[i,0] = float(words[1])*angstrom
        coordinates[i,1] = float(words[2])*angstrom
        coordinates[i,2] = float(words[3])*angstrom
    f.close()
    return {
        'coordinates': coordinates,
        'numbers': numbers
    }


def dump_xyz(filename, data):
    '''Write a molecule to a .xyz file.

       **Arguments:**

       filename
            The name of the file to be written. This usually the extension
            ".xyz".

       data
            A dictionary with molecule data. Must contain ``coordinates`` and
            ``numbers``.
    '''
    coordinates, numbers = typecheck_dump(data, ['coordinates', 'numbers'])
    numbers = data['numbers']
    natom = len(numbers)
    with open(filename, 'w') as f:
        print >> f, natom
        print >> f, 'File generated with Horton'
        for i in xrange(natom):
            n = periodic[numbers[i]].symbol
            x, y, z = coordinates[i]/angstrom
            print >> f, '%2s %15.10f %15.10f %15.10f' % (n, x, y, z)
