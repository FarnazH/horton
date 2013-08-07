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
'''EDIIS+DIIS Self-Consistent Field algorithm'''

import numpy as np

from horton.log import log, timer
from horton.exceptions import NoSCFConvergence
from horton.meanfield.wfn import RestrictedWFN
from horton.meanfield.scf_diis import DIISHistory, converge_scf_diis_cs
from horton.meanfield.scf_cdiis import solve_cdiis, PulayDIISHistory
from horton.meanfield.scf_ediis import EnergyDIISHistory
from horton.quadprog import QPSolver


__all__ = ['converge_scf_ediis2']


@timer.with_section('SCF')
def converge_scf_ediis2(ham, maxiter=128, threshold=1e-6, nvector=6, prune_old_states=True):
    '''Minimize the energy of the wavefunction with the EDIIS+DIIS algorithm

       **Arguments:**

       ham
            A Hamiltonian instance.

       **Optional arguments:**

       maxiter
            The maximum number of iterations. When set to None, the SCF loop
            will go one until convergence is reached.

       threshold
            The convergence threshold for the wavefunction

       prune_old_states
            When set to True, old states are pruned from the history when their
            coefficient is zero. Pruning starts at the oldest state and stops
            as soon as a state is encountered with a non-zero coefficient. Even
            if some newer states have a zero coefficient.

       **Raises:**

       NoSCFConvergence
            if the convergence criteria are not met within the specified number
            of iterations.
    '''
    log.cite('kudin2002', 'using the EDIIS+DIIS SCF algorithm')
    if isinstance(ham.system.wfn, RestrictedWFN):
        converge_scf_ediis2_cs(ham, maxiter, threshold, nvector, prune_old_states)
    else:
        raise NotImplementedError


def converge_scf_ediis2_cs(ham, maxiter=128, threshold=1e-6, nvector=6, prune_old_states=True):
    '''Minimize the energy of the closed-shell wavefunction with EDIIS+DIIS

       **Arguments:**

       ham
            A Hamiltonian instance.

       **Optional arguments:**

       maxiter
            The maximum number of iterations. When set to None, the SCF loop
            will go one until convergence is reached.

       threshold
            The convergence threshold for the wavefunction

       prune_old_states
            When set to True, old states are pruned from the history when their
            coefficient is zero. Pruning starts at the oldest state and stops
            as soon as a state is encountered with a non-zero coefficient. Even
            if some newer states have a zero coefficient.

       **Raises:**

       NoSCFConvergence
            if the convergence criteria are not met within the specified number
            of iterations.
    '''
    log.cite('kudin2002', 'For the use of the EDIIS+DIIS method.')
    converge_scf_diis_cs(ham, EnergyDIIS2History, maxiter, threshold, nvector, prune_old_states)


class EnergyDIIS2History(EnergyDIISHistory, PulayDIISHistory):
    '''A EDIIS+DIIS history object that keeps track of previous SCF solutions

       This method uses EDIIS for the first iterations and switches to CDIIS
       to as soon as some initial degree of convergence is achieved.
    '''
    name = 'EDIIS+DIIS'
    need_energy = True

    def __init__(self, lf, nvector, overlap):
        '''
           **Arguments:**

           lf
                The LinalgFactor used to create the one-body operators.

           nvector
                The maximum size of the history.

           overlap
                The overlap matrix of the system.
        '''
        # for the EDIIS part
        self.edots = np.empty((nvector, nvector))
        self.edots.fill(np.nan)
        # for the CDIIS part
        self.cdots = np.empty((nvector, nvector))
        self.cdots.fill(np.nan)
        DIISHistory.__init__(self, lf, nvector, overlap, [self.edots, self.cdots])

    def get_fns(self):
        '''Rescaled function values assiociated with each state in the stack.'''
        if self.stack[self.nused-1].norm < 1e-2:
            return PulayDIISHistory.get_fns(self)
        else:
            return EnergyDIISHistory.get_fns(self)

    def solve(self, dm_output, fock_output):
        '''Extrapolate a new density and/or fock matrix that should have the smallest commutator norm.

           **Arguments:**

           dm_output
                The output for the density matrix. If set to None, this is
                argument is ignored.

           fock_output
                The output for the Fock matrix. If set to None, this is
                argument is ignored.
        '''
        if self.stack[self.nused-1].norm < 1e-2:
            return PulayDIISHistory.solve(self, dm_output, fock_output)
        else:
            return EnergyDIISHistory.solve(self, dm_output, fock_output)
