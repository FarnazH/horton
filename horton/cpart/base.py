# -*- coding: utf-8 -*-
# Horton is a moldens Functional Theory program.
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


import numpy as np

from horton.cache import JustOnceClass, just_once, Cache
from horton.log import log, timer


__all__ = ['CPart']


class CPart(JustOnceClass):
    '''Base class for density partitioning schemes of cube files'''

    name = None
    options = ['smooth']

    def __init__(self, system, ui_grid, moldens, store, smooth):
        '''
           **Arguments:**

           system
                The system to be partitioned.

           ui_grid
                The uniform integration grid based on the cube file.

           moldens
                The all-electron density grid data.

           store
                An instance of the class ArrayStore to store large working arrays

           **Optional arguments:**

           smooth
                When set to True, no corrections are included to integrate
                the cusps.
        '''
        JustOnceClass.__init__(self)

        self._system = system
        self._ui_grid = ui_grid
        self._smooth = smooth

        # ArrayStore is used to avoid recomputation of huge arrays. This is not
        # always desirable due to memory constraints. Therefore the arrays
        # can be stored in a file or not stored at all. (See ArrayStore for
        # more details.) The convention is cpart is to use the store for large
        # arrays whose number scales with the system size, e.g. pro-atoms and
        # AIM densities. All other arrays are stored in the cache. This means
        # that after the initial setup of the pro-atoms, the partitioning schemes
        # must store sufficient details to recreate the proatoms when needed
        self._store = store

        # Caching stuff, to avoid recomputation of earlier results
        self._cache = Cache()
        self._cache.dump('moldens', moldens)

        # Some screen logging
        self._init_log()

        if not smooth:
            with timer.section('CPart wcor'):
                self._init_weight_corrections()
        with timer.section('CPart setup'):
            self._init_partitioning()

    def __getitem__(self, key):
        return self._cache.load(key)

    def _get_system(self):
        return self._system

    system = property(_get_system)

    def _get_ui_grid(self):
        return self._ui_grid

    ui_grid = property(_get_ui_grid)

    def _get_smooth(self):
        return self._smooth

    smooth = property(_get_smooth)

    def _init_partitioning(self):
        # This routine must prepare the partitioning such that the atomic weight
        # functions can be quickly recomputed if they can not be loaded from
        # the store.
        raise NotImplementedError

    def _init_weight_corrections(self):
        raise NotImplementedError

    def _init_log(self):
        if log.do_medium:
            log('Performing a density-based AIM analysis of a cube file.')
            log.deflist([
                ('System', self._system),
                ('Uniform Integration Grid', self._ui_grid),
                ('Grid shape', self._ui_grid.shape),
                ('Mean spacing', '%10.5e' % (self._ui_grid.grid_cell.volume**(1.0/3.0))),
            ])

    def get_wcor(self):
        if self._cache.has('wcor'):
            return self._cache.load('wcor')

    def zeros(self):
        return np.zeros(self._ui_grid.shape)

    def get_at_weights(self, index, output):
        # The default behavior is load the weights from the store. If this fails,
        # they must be recomputed.
        present = self._store.load(output, 'at_weights', index)
        if not present:
            self.compute_at_weights(index, output)
            self._store.dump(output, 'at_weights', index)

    def compute_at_weights(self, index, output):
        raise NotImplementedError

    def compute_pseudo_population(self, index, work=None):
        if work is None:
            work = self.zeros()
        moldens = self._cache.load('moldens')
        wcor = self.get_wcor()
        self.get_at_weights(index, work)
        return self._ui_grid.integrate(wcor, work, moldens)

    def do_all(self):
        '''Computes all reasonable properties and returns a corresponding list of keys'''
        self.do_populations()
        self.do_charges()
        return ['populations', 'charges']

    @just_once
    def do_populations(self):
        if log.do_medium:
            log('Computing atomic populations.')
        populations, new = self._cache.load('populations', alloc=self.system.natom)
        if new:
            work = self.zeros()
            for i in xrange(self._system.natom):
                populations[i] = self.compute_pseudo_population(i, work)
            # correct for pseudo-potentials
            populations += self.system.numbers - self.system.pseudo_numbers

    @just_once
    def do_charges(self):
        self.do_populations()
        if log.do_medium:
            log('Computing atomic charges.')
        charges, new = self._cache.load('charges', alloc=self.system.natom)
        if new:
            populations = self._cache.load('populations')
            charges[:] = self.system.numbers - populations
