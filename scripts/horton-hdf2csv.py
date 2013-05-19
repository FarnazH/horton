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


import sys, argparse, os, csv

import h5py as h5, numpy as np
from horton.log import log
from horton.scripts.common import parse_h5
from horton.scripts.hdf2csv import iter_datasets


epilog = '''\
This script was added for the sake of convience for those who are not capable to
process the output of horton scripts written in HDF5 format directly. If you
know how, please process the HDF5 files directly with custom scripts. That is
far easier than interfacing to the CSV files that this script generates. The
h5py library, see http://www.h5py.org/, is a great tool to make such custom
scripts.
'''

def parse_args():
    parser = argparse.ArgumentParser(prog='horton-hdf2csv.py',
        description='Convert part of a HDF5 file to a CSV file, suitable for spreadsheets.',
        epilog=epilog)

    parser.add_argument('h5',
        help='[HDF5 filename]:[HDF5 group] Specifies the part of the HDF5 file '
             'that gets converted.')
    parser.add_argument('csv',
        help='The name of the comma-separate value output file.')

    return parser.parse_args()


def main():
    args = parse_args()

    fn_h5, grp_name = parse_h5(args.h5)
    with h5.File(fn_h5, 'r') as fin, open(args.csv, 'w') as fout:
        w = csv.writer(fout)
        w.writerow(['Converted data from %s' % args.h5])
        w.writerow([])
        for name, dset in iter_datasets(fin[grp_name]):
            if len(dset.shape) > 3:
                if log.do_warning:
                    log.warn('Skipping %s because it has more than three axes.' % name)
            else:
                log('Converting %s' % name)

            w.writerow(['Dataset', name])
            w.writerow(['Shape'] + list(dset.shape))
            if len(dset.shape) == 0:
                w.writerow([dset[()]])
            elif len(dset.shape) == 1:
                for value in dset:
                    w.writerow([value])
            elif len(dset.shape) == 2:
                for row in dset:
                    w.writerow([value for value in row])
            elif len(dset.shape) == 3:
                for array in dset:
                    l = []
                    for col in array.T:
                        for value in col:
                            l.append(value)
                        l.append('')
                    del l[-1]
                    w.writerow(l)
            else:
                w.writerow(['Skipped because ndim=%i>3' % len(dset.shape)])
            w.writerow([])


if __name__ == '__main__':
    main()
