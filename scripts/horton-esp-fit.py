#!/usr/bin/env python
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


import sys, argparse, os

import h5py as h5, numpy as np
from horton import System, ESPCost, log, dump_hdf5_low, symmetry_analysis
from horton.scripts.common import parse_h5, store_args, safe_open_h5


def parse_args():
    parser = argparse.ArgumentParser(prog='horton-esp-fit.py',
        description='Estimate charges from an ESP cost function.')

    parser.add_argument('h5',
        help='[HDF5 filename]:[HDF5 group] The HDF5 file can be created with '
             'horton-esp-cost.py. The group must contain matrices A, B and C '
             'that define the quadratic cost function. The HDF5 file must also '
             'contain a system group in which the atoms are defined with an '
             'array numbers (for the atom numbers) and an array coordinates.')
    parser.add_argument('group',
        help='All results will be stored in this subgroup.')
    parser.add_argument('--qtot', '-q', default=0.0, type=float,
        help='The total charge of the system. [default=%(default)s]')
    parser.add_argument('--ridge', default=0.0, type=float,
        help='The thikonov regularization strength used when solving the '
             'charges. [default=%(default)s]')
    parser.add_argument('--symmetry', default=None, type=str,
        help='Perform a symmetry analysis on the charges. This option '
             'requires one argument: a CIF file with the generators of the '
             'symmetry of this system and a primitive unit cell.')

    # TODO: more constraint and restraint options
    # TODO: When no group is given in h5 argument, run over all groups that
    #       contain A, B and C.

    return parser.parse_args()


def main():
    args = parse_args()

    # Load the cost function from the HDF5 file
    fn_h5, grp_name = parse_h5(args.h5)
    with h5.File(fn_h5, 'r') as f:
        grp = f[grp_name]
        sys = System.from_file(f['system'], chk=None)
        cost = ESPCost(grp['A'][:], grp['B'][:], grp['C'][()], sys.natom)

    # Find the optimal charges
    results = {}
    results['x'] = cost.solve(args.qtot, args.ridge)
    results['charges'] = results['x'][:cost.natom]

    # Related properties
    results['cost'] = cost.value(results['x'])
    if results['cost'] < 0:
        results['rmsd'] = 0.0
    else:
        results['rmsd'] = results['cost']**0.5

    # Worst case stuff
    results['cost_worst'] = cost.worst(args.qtot)
    if results['cost_worst'] < 0:
        results['rmsd_worst'] = 0.0
    else:
        results['rmsd_worst'] = results['cost_worst']**0.5

    # Write some things on screen
    if log.do_medium:
        log('Important parameters:')
        log.hline()
        log('RMSD charges:                  %10.5e' % np.sqrt((results['charges']**2).mean()))
        log('RMSD ESP:                      %10.5e' % results['rmsd'])
        log('Worst RMSD ESP:                %10.5e' % results['rmsd_worst'])
        log.hline()

    # Perform a symmetry analysis if requested
    if args.symmetry is not None:
        sys_sym = System.from_file(args.symmetry)
        sym = sys_sym.props.get('symmetry')
        if sym is None:
            raise ValueError('No symmetry information found in %s.' % args.symmetry)
        sys_results = {'charges': results['charges']}
        sym_results = symmetry_analysis(sys, sym, sys_results)
        results['symmetry'] = sym_results
        sys.props['symmetry'] = sym

    # Store the results in an HDF5 file
    with safe_open_h5(fn_h5) as f:
        # rewrite system in case of symmetry analysis
        if args.symmetry is not None:
            del f['system']
            sys.to_file(f.create_group('system'))

        # Store results
        dump_hdf5_low(f[grp_name], args.group, results)

        # Store command line arguments
        store_args(args, f[grp_name][args.group])

        if log.do_medium:
            log('Results written to %s:%s/%s' % (fn_h5, grp_name, args.group))


if __name__ == '__main__':
    main()
