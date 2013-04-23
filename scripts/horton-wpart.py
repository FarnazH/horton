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

import h5py as h5
from horton import System, wpart_schemes, Cell, ProAtomDB, log, BeckeMolGrid, \
    lebedev_laikov_npoints
from horton.scripts.common import store_args, safe_open_h5
from horton.scripts.wpart import parse_grid


def parse_args():
    parser = argparse.ArgumentParser(prog='horton-wpart.py',
        description='Partition the density from a wavefunction file.')

    parser.add_argument('wfn',
        help='The wfn file. Supported formats: fchk, mkl, molden.input')
    parser.add_argument('scheme', choices=wpart_schemes.keys(),
        help='The scheme to be used for the partitioning')
    parser.add_argument('atoms',
        help='An HDF5 file with atomic reference densities.')

    parser.add_argument('--overwrite', default=False, action='store_true',
        help='Overwrite existing output in the HDF5 file')
    parser.add_argument('--debug', default=False, action='store_true',
        help='Add additional internal results to a debug subgroup.')
    parser.add_argument('--suffix', default=None, type=str,
        help='Add an additional suffix to the HDF5 output group.')

    parser.add_argument('--grid', type=str, default='coarse',
        help='Choose the accuracy of the integration grid. Four built-in tuned '
             'grids are available: coarse, medium, fine, veryfine. '
             '[default=%%(default)s] These are applicable when the system '
             'contains only elements up to argon. In other cases, an integer '
             'can be provided that sets the number of angular (Lebedev-Laikov) '
             'grid points. Choose a number from %s. The radial grid is then '
             'take identical to the one used in the proatom database.' %
             (" ".join(str(i) for i in lebedev_laikov_npoints)))
    parser.add_argument('--global', dest='local', default=True, action='store_false',
        help='Use the entire molecular grid for all integrations. The default '
             'behavior is to compute the integral for a given atom on a '
             'atom-centered grid, which is a part of the molecular grid.')
    parser.add_argument('--maxiter', '-i', default=500, type=int,
        help='The maximum allowed number of iterations. [default=%(default)s]')
    parser.add_argument('--threshold', '-t', default=1e-6, type=float,
        help='The iterative scheme is converged when the maximum change of '
             'the charges between two iterations drops below this threshold. '
             '[default=%(default)s]')

    return parser.parse_args()


def main():
    args = parse_args()

    # check if the folder is already present in the output file
    fn_h5 = args.wfn + '.h5'
    grp_name = args.scheme
    if args.suffix is not None:
        grp_name += '_' + args.suffix

    if os.path.isfile(fn_h5):
        with h5.File(fn_h5, 'r') as f:
            if 'wpart/%s' % grp_name in f and not args.overwrite:
                if log.do_warning:
                    log.warn('Skipping because "%s" is already present in the output.' % grp_name)
                return

    # Load the system
    sys = System.from_file(args.wfn)

    # Load the proatomdb
    proatomdb = ProAtomDB.from_file(args.atoms)

    # Run the partitioning
    WPartClass = wpart_schemes[args.scheme]
    kwargs = dict((key, val) for key, val in vars(args).iteritems() if key in WPartClass.options)
    atspecs = parse_grid(args.grid, sys, proatomdb)
    molgrid = BeckeMolGrid(sys, atspecs, keep_subgrids=int(args.local))
    wpart = wpart_schemes[args.scheme](sys, molgrid, proatomdb, **kwargs)
    names = wpart.do_all()

    # Store the results in an HDF5 file
    with safe_open_h5(fn_h5) as f:
        # Store system
        sys_grp = f.require_group('system')
        sys.to_file(sys_grp)

        # Store results
        grp_wpart = f.require_group('wpart')
        if grp_name in grp_wpart:
            del grp_wpart[grp_name]
        grp = grp_wpart.create_group(grp_name)
        for name in names:
            grp[name] = wpart[name]

        # Store command line arguments
        store_args(args, grp)

        if args.debug:
            # Store additional data for debugging
            if 'debug' in grp:
                del grp['debug']
            grp_debug = grp.create_group('debug')
            for debug_key in wpart.cache._store:
                debug_name = '_'.join(str(x) for x in debug_key)
                if debug_name not in names:
                    grp_debug[debug_name] = wpart.cache.load(*debug_key)


if __name__ == '__main__':
    main()
