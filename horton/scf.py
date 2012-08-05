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


from horton.wfn import ClosedShellWFN, OpenShellWFN


__all__ = ['converge_scf']


def converge_scf(ham, max_iter=128, threshold=1e-8):
    '''Minimize the energy of the wavefunction with basic SCF

       **Arguments:**

       ham
            A Hamiltonian instance.

       **Optional arguments:**

       max_iter
            The maximum number of iterations

       threshold
            The convergence threshold for the wavefunction
    '''
    if isinstance(ham.system.wfn, ClosedShellWFN):
        converge_scf_cs(ham, max_iter, threshold)
    elif isinstance(ham.system.wfn, OpenShellWFN):
        converge_scf_os(ham, max_iter, threshold)
    else:
        raise NotImplementedError


def converge_scf_cs(ham, max_iter=128, threshold=1e-8):
    '''Minimize the energy of the wavefunction with basic closed-shell SCF

       **Arguments:**

       ham
            A Hamiltonian instance.

       **Optional arguments:**

       max_iter
            The maximum number of iterations

       threshold
            The convergence threshold for the wavefunction
    '''
    lf = ham.system.lf
    wfn = ham.system.wfn
    nbasis = ham.system.obasis.nbasis
    fock = lf.create_one_body(nbasis)
    dm = lf.create_one_body(nbasis)
    for i in xrange(max_iter):
        # Construct the Fock operator
        fock.reset()
        wfn.compute_density_matrix(dm)
        ham.compute_fock(dm, None, None, fock, None)
        # Check for convergence
        error = lf.error_eigen(fock, ham.overlap, wfn.expansion)
        if error < threshold:
            break
        # Diagonalize the fock operator
        lf.diagonalize(fock, ham.overlap, wfn.expansion)
        # Write intermediate results to checkpoint
        ham.system.update_chk('wfn')



def converge_scf_os(ham, max_iter=128, threshold=1e-8):
    '''Minimize the energy of the wavefunction with basic open-shell SCF

       **Arguments:**

       ham
            A Hamiltonian instance.

       **Optional arguments:**

       max_iter
            The maximum number of iterations

       threshold
            The convergence threshold for the wavefunction
    '''
    lf = ham.system.lf
    wfn = ham.system.wfn
    nbasis = ham.system.obasis.nbasis
    fock_alpha = lf.create_one_body(nbasis)
    fock_beta = lf.create_one_body(nbasis)
    dm_alpha = lf.create_one_body(nbasis)
    dm_beta = lf.create_one_body(nbasis)
    dm_full = lf.create_one_body(nbasis)
    for i in xrange(max_iter):
        # Construct the Fock operators
        fock_alpha.reset()
        fock_beta.reset()
        wfn.compute_alpha_density_matrix(dm_alpha)
        wfn.compute_beta_density_matrix(dm_beta)
        dm_full.reset()
        dm_full.iadd(dm_alpha)
        dm_full.iadd(dm_beta)
        ham.compute_fock(dm_alpha, dm_beta, dm_full, fock_alpha, fock_beta)
        # Check for convergence
        error_alpha = lf.error_eigen(fock_alpha, ham.overlap, wfn.alpha_expansion)
        error_beta = lf.error_eigen(fock_beta, ham.overlap, wfn.beta_expansion)
        if error_alpha < threshold and error_beta < threshold:
            break
        # Diagonalize the fock operators
        lf.diagonalize(fock_alpha, ham.overlap, wfn.alpha_expansion)
        lf.diagonalize(fock_beta, ham.overlap, wfn.beta_expansion)
        # Write intermediate results to checkpoint
        ham.system.update_chk('wfn')
