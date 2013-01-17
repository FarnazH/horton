#!/usr/bin/env python


from horton import *

# Loading system
system = System.from_file('water.xyz', obasis='3-21G')

# Allocate wavefuntion
system.init_wfn(charge=0, mult=1)

# Initial guess
guess_hamiltonian_core(system)

# Setup integration grids with default settings
grid = BeckeMolGrid(system)

# Construction of Hamiltonian
ham = Hamiltonian(system, [Hartree(), DiracExchange()], grid)

# Optimal damping SCF cycle
converged = converge_scf_oda(ham)

# Energy computation
log.set_level(log.high)
ham.compute_energy()
log.set_level(log.medium)

