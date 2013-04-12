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


from string import Template as BaseTemplate
from glob import glob
import re, os, stat, numpy as np, h5py as h5

from horton import periodic, log, System, ProAtomRecord


__all__ = [
    'iter_elements', 'iter_mults', 'iter_states',
    'Template', 'EnergyTable', 'atom_programs',
]


def iter_elements(elements_str):
    '''Interpret a string as a list of elements

       elements_str
            A string with comma-separated element numbers. One may add ranges
            with the format 'N-M' where M>N.
    '''
    for item in elements_str.split(','):
        if '-' in item:
            words = item.split("-")
            if len(words) != 2:
                raise ValueError("Each item should contain at most one dash.")
            first = int(words[0])
            last = int(words[1])
            if first > last:
                raise ValueError('first=%i > last=%i' % (first, last))
            for number in xrange(first,last+1):
                yield number
        else:
            yield int(item)


# Presets for spin multiplicites. The first element is according to Hund's rule.
# Following elements are reasonable.
mult_presets = {
    1: [2],
    2: [1, 3],
    3: [2, 4],
    4: [1, 3],
    5: [2, 4],
    6: [3, 5, 1],
    7: [4, 2],
    8: [3, 1],
    9: [2],
    10: [1],
    11: [2],
    12: [1, 3],
    13: [2, 4],
    14: [3, 5, 1],
    15: [4, 2],
    16: [3, 1],
    17: [2],
    18: [1],
    19: [2],
    20: [1, 3],
    21: [2, 4],
    22: [3, 5, 1],
    23: [4, 6, 2],
    24: [7, 5, 3, 1],
    25: [6, 4, 2],
    26: [5, 3, 1],
    27: [4, 2],
    28: [3, 1],
    29: [2],
    30: [1],
    31: [2, 4, 6],
    32: [3, 1, 5],
    33: [4, 2],
    34: [3, 1],
    35: [2],
    36: [1],
    37: [2],
    38: [1, 3],
    39: [2, 4],
    40: [3, 1, 5],
    41: [6, 4, 2],
    42: [7, 5, 3, 1],
    43: [6, 4, 2],
    44: [5, 3, 1],
    45: [4, 2],
    46: [1, 3],
    47: [2],
    48: [1],
    49: [2, 4],
    50: [3, 1, 5],
    51: [4, 2],
    52: [3, 1],
    53: [2],
    54: [1],
    55: [2],
    56: [1, 3],
}


def iter_mults(nel, hund):
    '''Iterate over atomic spin multiplicites for the given number of electrons

       **Arguments:**

       nel
            The number of electrons (1-56)

       hund
            When set to True, only one spin multiplicity is returned. Otherwise
            several reasonable spin multiplicities are given.
    '''

    if hund:
        yield mult_presets[nel][0]
    else:
        for mult in mult_presets[nel]:
            yield mult


def iter_states(elements, max_kation, max_anion, hund):
    '''Iterate over all requested atomic states

       **Arguments:**

       elements
            A string that is suitable for ``iter_elements``

       template
            An instance of the ``atomdb.Template`` class

       max_kation
            The limit for the most positive kation

       max_anion
            The limit for the most negative anion

       hund
            Flag to adhere to hund's rule for the spin multiplicities.
    '''
    for number in iter_elements(elements):
        # Loop over all charge states for this element
        for charge in xrange(-max_anion, max_kation+1):
            nel = number - charge
            if nel <= 0:
                continue
            # loop over multiplicities
            for mult in iter_mults(nel, hund):
                yield number, charge, mult


class Template(BaseTemplate):
    '''A template with modifications to support inclusion of other files.'''
    idpattern = r'[_a-z0-9.:-]+'

    def __init__(self, *args, **kwargs):
        BaseTemplate.__init__(self, *args, **kwargs)
        self._init_include_names()
        self._load_includes()

    def _init_include_names(self):
        '''Return a list of include variables

           The include variables in the template are variables of the form
           ${file:name} or ${line:name}. This routine lists all the names
           encountered. Duplicates are eliminated.
        '''
        pattern = '%s{(?P<braced>%s)}' % (re.escape(self.delimiter), self.idpattern)
        file_names = set([])
        line_names = set([])
        for mo in re.finditer(pattern, self.template):
            braced = mo.group('braced')
            if braced is not None and braced.startswith('file:'):
                file_names.add(braced[5:])
            if braced is not None and braced.startswith('line:'):
                line_names.add(braced[5:])
        self.file_names = list(file_names)
        self.line_names = list(line_names)

    def _load_includes(self):
        '''Load included files for a given element number'''
        self.includes = []
        # Load files
        for name in self.file_names:
            records = []
            for fn in sorted(glob('%s.[0-9][0-9][0-9]_[0-9][0-9]_[0-9][0-9]'))[:-1]:
                with open(fn) as f:
                    s = f.read()
                    # chop of one final newline if present (mostly the case)
                    if s[-1] == '\n':
                        s = s[:-1]
                number = int(fn[-10:-7])
                pop = int(fn[-6:-3])
                mult = int(fn[-2:])
                records.append((number, pop, mult, s))
            self.includes.append((name, 'file', records))
        # Load lines
        for name in self.line_names:
            with open(name) as f:
                records = []
                for line in f:
                    # ignore empty lines
                    if len(line.strip()) == 0:
                        continue
                    number = int(line[:3])
                    assert line[3] == '_'
                    pop = int(line[4:7])
                    assert line[7] == '_'
                    mult = int(line[8:10])
                    assert line[10] == ' '
                    s = line[11:-1]
                    records.append((number, pop, mult, s))
            self.includes.append((name, 'line', records))

    def _log_includes(self):
        # log the include names
        if len(self.file_names) + len(self.line_names) > 0 and log.do_medium:
            log('The following includes were detected in the template:')
            for name, kind, records in self.includes:
                log('   %s (%s)' % (name, kind))
                for n, p, m, s in self.includes[name]:
                    log('      %03i_%03i_%02i' % (n, p, m))

    def get_subs(self, number, pop, mult):
        subs = {}
        for name, kind, records in self.includes:
            found_s = None
            for n, p, m, s in records:
                if ((n==0) or (number==n)) and ((p==0) or (pop==p)) and ((m==0) or (mult==m)):
                    # match
                    found_s = s
                    break
            if found_s is None:
                raise KeyError('No matching include found for \'%s\' (%03i_%03i_%02i)' % (name, number, pop, mult))
            subs['%s:%s' % (kind, name)] = s
        return subs


class EnergyTable(object):
    def __init__(self):
        self.all = {}

    def add(self, number, pop, energy):
        cases = self.all.setdefault(number, {})
        cases[pop] = energy

    def log(self):
        log(' Nr Pop Chg              Energy          Ionization            Affinity')
        log.hline()
        for number, cases in sorted(self.all.iteritems()):
            for pop, energy in sorted(cases.iteritems()):
                energy_prev = cases.get(pop-1)
                if energy_prev is None:
                    ip_str = ''
                else:
                    ip_str = '% 18.10f' % (energy_prev - energy)

                energy_next = cases.get(pop+1)
                if energy_next is None:
                    ea_str = ''
                else:
                    ea_str = '% 18.10f' % (energy - energy_next)

                log('%3i %3i %+3i  % 18.10f  %18s  %18s' % (
                    number, pop, number-pop, energy, ip_str, ea_str
                ))
            log.blank()


class AtomProgram(object):
    name = None
    run_script = None

    def write_input(self, number, charge, mult, template, do_overwrite, atgrid):
        # Directory stuff
        nel = number - charge
        dn_mult = '%03i_%s_%03i_q%+03i/mult%02i' % (
            number, periodic[number].symbol.lower().rjust(2, '_'), nel, charge, mult)

        # Figure out if we want to write
        fn_inp = '%s/atom.in' % dn_mult
        exists = os.path.isfile(fn_inp)
        do_write = not exists or do_overwrite

        if do_write:
            try:
                subs = template.get_subs(number, nel, mult)
            except KeyError:
                if log.do_warning:
                    log.warn('Could not find all subs for %03i.%03i.%03i. Skipping.' % (number, nel, mult))
                return dn_mult, False
            if not os.path.isdir(dn_mult):
                os.makedirs(dn_mult)
            with open(fn_inp, 'w') as f:
                f.write(template.substitute(
                    subs,
                    charge=str(charge),
                    mult=str(mult),
                    number=str(number),
                    element=periodic[number].symbol,
                ))
            if log.do_medium:
                if exists:
                    log('Overwritten:      ', fn_inp)
                else:
                    log('Written new:      ', fn_inp)
        elif log.do_medium:
            log('Not overwriting:  ', fn_inp)

        return dn_mult, do_write

    def write_run_script(self):
        # write the script
        fn_script = 'run_%s.sh' % self.name
        with open(fn_script, 'w') as f:
            print >> f, self.run_script
            for dn in sorted(glob("[01]??_??_[01]??_q[+-]??/mult??")):
                print >> f, 'do_atom', dn
        # make the script executable
        os.chmod(fn_script, stat.S_IXUSR | os.stat(fn_script).st_mode)
        if log.do_medium:
            log('Written', fn_script)

    def _get_energy(self, system, dn_mult):
        return system.props['energy']

    def load_atom(self, dn_mult, ext):
        fn = '%s/atom.%s' % (dn_mult, ext)
        if not os.path.isfile(fn):
            return None, None

        system = System.from_file(fn)
        energy = self._get_energy(system, dn_mult)
        return system, energy

    def create_record(self, system, dn_mult, atgrid):
        if system is None:
            raise NotImplementedError

        return ProAtomRecord.from_system(system, atgrid)


run_gaussian_script = '''
#!/bin/bash

# make sure %(name)s is available before running this script.

MISSING=0
if ! which %(name)s &>/dev/null; then echo "%(name)s binary not found."; MISSING=1; fi
if [ $MISSING -eq 1 ]; then echo "The required programs are not present on your system. Giving up."; exit -1; fi

function do_atom {
    echo "Computing in ${1}"
    cd ${1}
    if [ -e atom.out ]; then
        echo "Output file present in ${1}, not recomputing."
    else
        %(name)s < atom.in > atom.out
        formchk atom.chk atom.fchk
        rm atom.chk
    fi
    cd -
}
'''


class G09AtomProgram(AtomProgram):
    name = 'g09'
    run_script = run_gaussian_script % {'name': 'g09'}

    def write_input(self, number, charge, mult, template, do_overwrite, atgrid):
        if '%chk=atom.chk\n' not in template.template:
            raise ValueError('The template must contain a line \'%chk=atom.chk\'')
        return AtomProgram.write_input(self, number, charge, mult, template, do_overwrite, atgrid)

    def load_atom(self, dn_mult):
        return AtomProgram.load_atom(self, dn_mult, 'fchk')


class G03AtomProgram(G09AtomProgram):
    name = 'g03'
    run_script = run_gaussian_script % {'name': 'g03'}


run_orca_script = '''
#!/bin/bash

# make sure orca and orca2mkl are available before running this script.

MISSING=0
if ! which orca &>/dev/null; then echo "orca binary not found."; MISSING=1; fi
if ! which orca_2mkl &>/dev/null; then echo "orca_2mkl binary not found."; MISSING=1; fi
if [ $MISSING -eq 1 ]; then echo "The required programs are not present on your system. Giving up."; exit -1; fi

function do_atom {
    echo "Computing in ${1}"
    cd ${1}
    if [ -e atom.out ]; then
        echo "Output file present in ${1}, not recomputing."
    else
        orca atom.in > atom.out
        orca_2mkl atom -molden
    fi
    cd -
}
'''


class OrcaAtomProgram(AtomProgram):
    name = 'orca'
    run_script = run_orca_script

    def _get_energy(self, system, dn_mult):
        with open('%s/atom.out' % dn_mult) as f:
            for line in f:
                if line.startswith('Total Energy       :'):
                    return float(line[25:43])

    def load_atom(self, dn_mult):
        return AtomProgram.load_atom(self, dn_mult, 'molden.input')


run_adf_script = '''
#!/bin/bash

# make sure adf and the kf2hdf.py script are available before running this
# script.

MISSING=0
if ! which adf &>/dev/null; then echo "adf binary not found."; MISSING=1; fi
if ! which densf &>/dev/null; then echo "densf binary not found."; MISSING=1; fi
if ! which kf2hdf.py &>/dev/null; then echo "kf2hdf.py not found."; MISSING=1; fi
if [ $MISSING -eq 1 ]; then echo "The required programs are not present on your system. Giving up."; exit -1; fi

function do_atom {
    echo "Computing in ${1}"
    cd ${1}
    if [ -e atom.out ]; then
        echo "Output file present in ${1}, not recomputing."
    else
        adf < atom.in > atom.out
        densf < grid.in > grid.out
        kf2hdf.py TAPE41 grid.h5
        rm logfile t21.* TAPE21 TAPE41
    fi
    cd -
}
'''

adf_grid_prefix = '''\
INPUTFILE TAPE21
UNITS
 Length bohr
END
Grid inline
'''

adf_grid_suffix = '''\
END
density scf
'''


class ADFAtomProgram(AtomProgram):
    name = 'adf'
    run_script = run_adf_script

    def write_input(self, number, charge, mult, template, do_overwrite, atgrid):
        dn_mult, do_write = AtomProgram.write_input(self, number, charge, mult, template, do_overwrite, atgrid)
        if do_write:
            # Write the grid input
            with open('%s/grid.in' % dn_mult, 'w') as f:
                f.write(adf_grid_prefix)
                for point in atgrid.points:
                    f.write('    %23.16e  %23.16e  %23.16e\n' % tuple(point))
                f.write(adf_grid_suffix)
        return dn_mult, do_write

    def _get_energy(self, system, dn_mult):
        with open('%s/atom.out' % dn_mult) as f:
            for line in f:
                if line.startswith('Total Bonding Energy:'):
                    return float(line[30:56])


    def load_atom(self, dn_mult):
        system = None
        return system, self._get_energy(system, dn_mult)

    def create_record(self, system, dn_mult, atgrid):
        with h5.File('%s/grid.h5' % dn_mult) as f:
            npoint = f['Grid/total nr of points'][()]
            assert npoint == atgrid.npoint
            llgrid = atgrid.subgrids[0]
            dens = f['SCF/Density'][:].reshape((-1,nll))
            record = np.dot(dens, llgrid.weights)/llgrid.weights.sum()
            return record


run_cp2k_script = '''
#!/bin/bash

# make sure cp2k.sdbg is in the path before running this script.

MISSING=0
if ! which cp2k.sdbg &>/dev/null; then echo "cp2k.sdbg binary not found."; MISSING=1; fi
if [ $MISSING -eq 1 ]; then echo "The required programs are not present on your system. Giving up."; exit -1; fi

function do_atom {
    echo "Computing in ${1}"
    cd ${1}
    if [ -e atom.cp2k.out ]; then
        echo "Output file present in ${1}, not recomputing."
    else
        cp2k.sdbg atom.in > atom.cp2k.out
    fi
    cd -
}
'''

class CP2KAtomProgram(AtomProgram):
    name = 'cp2k'
    run_script = run_cp2k_script

    def write_input(self, number, charge, mult, template, do_overwrite, atgrid):
        if '&ATOM' not in template.template:
            raise ValueError('The template must be a CP2K atom input. (\'&ATOM\' not found.)')
        return AtomProgram.write_input(self, number, charge, mult, template, do_overwrite, atgrid)

    def load_atom(self, dn_mult):
        return AtomProgram.load_atom(self, dn_mult, 'cp2k.out')



atom_programs = {}
for APC in globals().values():
    if isinstance(APC, type) and issubclass(APC, AtomProgram) and not APC is AtomProgram:
        atom_programs[APC.name] = APC()
