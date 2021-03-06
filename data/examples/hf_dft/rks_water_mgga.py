#!/usr/bin/env python
#JSON {"lot": "RKS/6-31G(d)",
#JSON  "scf": "CDIISSCFSolver",
#JSON  "er": "cholesky",
#JSON  "difficulty": 6,
#JSON  "description": "Basic RKS DFT example with MGGA exhange-correlation functional (TPSS)"}

import numpy as np
from horton import *  # pylint: disable=wildcard-import,unused-wildcard-import


# Load the coordinates from file.
# Use the XYZ file from HORTON's test data directory.
fn_xyz = context.get_fn('test/water.xyz')
mol = IOData.from_file(fn_xyz)

# Create a Gaussian basis set
obasis = get_gobasis(mol.coordinates, mol.numbers, '6-31g(d)')

# Compute Gaussian integrals
olp = obasis.compute_overlap()
kin = obasis.compute_kinetic()
na = obasis.compute_nuclear_attraction(mol.coordinates, mol.pseudo_numbers)
er_vecs = obasis.compute_electron_repulsion_cholesky()

# Define a numerical integration grid needed the XC functionals
grid = BeckeMolGrid(mol.coordinates, mol.numbers, mol.pseudo_numbers)

# Create alpha orbitals
orb_alpha = Orbitals(obasis.nbasis)

# Initial guess
guess_core_hamiltonian(olp, kin + na, orb_alpha)

# Construct the restricted HF effective Hamiltonian
external = {'nn': compute_nucnuc(mol.coordinates, mol.pseudo_numbers)}
terms = [
    RTwoIndexTerm(kin, 'kin'),
    RDirectTerm(er_vecs, 'hartree'),
    RGridGroup(obasis, grid, [
        RLibXCMGGA('x_tpss'),
        RLibXCMGGA('c_tpss'),
    ]),
    RTwoIndexTerm(na, 'ne'),
]
ham = REffHam(terms, external)

# Decide how to occupy the orbitals (5 alpha electrons)
occ_model = AufbauOccModel(5)

# Converge WFN with CDIIS SCF
# - Construct the initial density matrix (needed for CDIIS).
occ_model.assign(orb_alpha)
dm_alpha = orb_alpha.to_dm()
# - SCF solver
scf_solver = CDIISSCFSolver(1e-6)
scf_solver(ham, olp, occ_model, dm_alpha)

# Derive orbitals (coeffs, energies and occupations) from the Fock and density
# matrices. The energy is also computed to store it in the output file below.
fock_alpha = np.zeros(olp.shape)
ham.reset(dm_alpha)
ham.compute_energy()
ham.compute_fock(fock_alpha)
orb_alpha.from_fock_and_dm(fock_alpha, dm_alpha, olp)

# Assign results to the molecule object and write it to a file, e.g. for
# later analysis. Note that the CDIIS algorithm can only really construct an
# optimized density matrix and no orbitals.
mol.title = 'RKS computation on water'
mol.energy = ham.cache['energy']
mol.obasis = obasis
mol.orb_alpha = orb_alpha
mol.dm_alpha = dm_alpha

# useful for post-processing (results stored in double precision):
mol.to_file('water.h5')


# CODE BELOW IS FOR horton-regression-test.py ONLY. IT IS NOT PART OF THE EXAMPLE.
rt_results = {
    'energy': ham.cache['energy'],
    'orb_alpha': orb_alpha.energies,
    'nn': ham.cache["energy_nn"],
    'kin': ham.cache["energy_kin"],
    'ne': ham.cache["energy_ne"],
    'grid': ham.cache["energy_grid_group"],
    'hartree': ham.cache["energy_hartree"],
}
# BEGIN AUTOGENERATED CODE. DO NOT CHANGE MANUALLY.
rt_previous = {
    'energy': -76.407936399996032,
    'orb_alpha': np.array([
        -18.88140274471057, -0.92689455671943777, -0.48003995365965246,
        -0.3068412737938469, -0.23305348781949642, 0.055765650587591052,
        0.13876252429050115, 0.78022341323374989, 0.82177783193535281,
        0.86268998494640037, 0.89541154561880765, 1.0425268139841128, 1.3431492859747944,
        1.7062096596569536, 1.7110987254283361, 1.7506809108152641, 2.2882571842385735,
        2.5849159392493357
    ]),
    'grid': -9.361522808603524,
    'hartree': 46.86311076030199,
    'kin': 76.04019446027614,
    'ne': -199.10689384840063,
    'nn': 9.1571750364299866,
}
