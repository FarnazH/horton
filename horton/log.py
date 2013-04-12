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
'''Screen logging, timing and citation management.

   The goal of the screen logger is to track the progress of a computation in
   a convenient human-readable way, possibly higlighting problematic situations.
   It is not intended as a computer-readable output file that contains all the
   results of a computation. For that purpose, all useful information is
   written to a binary checkpoint file or kept in memory as attributes of the
   Horton objects.
'''

# TODO: - use the logger in all current code

import sys, os, datetime, getpass, time, codecs, locale, atexit, traceback, \
    resource
from contextlib import contextmanager
import horton


__all__ = ['log', 'timer']


class ScreenLog(object):
    # log levels
    silent = 0
    warning = 1
    low = 2
    medium = 3
    high = 4
    debug = 5

    # screen parameter
    width = 80

    def __init__(self, name, version, head_banner, foot_banner, timer, f=None):
        self.name = name
        self.version = version
        self.head_banner = head_banner
        self.foot_banner = foot_banner
        self.timer = timer

        self._biblio = None
        self.mem = MemoryLogger(self)
        self._active = False
        self._level = self.medium
        self._last_used_location = None
        self.add_newline = False
        if f is None:
            _file = sys.stdout
        else:
            _file = f
        # Wrap sys.stdout into a StreamWriter to allow writing unicode.
        self._file = codecs.getwriter(locale.getpreferredencoding())(_file)

    do_warning = property(lambda self: self._level >= self.warning)
    do_low = property(lambda self: self._level >= self.low)
    do_medium = property(lambda self: self._level >= self.medium)
    do_high = property(lambda self: self._level >= self.high)
    do_debug = property(lambda self: self._level >= self.debug)

    def set_level(self, level):
        if level < self.silent or level > self.debug:
            raise ValueError('The level must be one of the ScreenLog attributes.')
        self._level = level

    def __call__(self, *words):
        s = u' '.join(unicode(w) for w in words)
        if not self.do_warning:
            raise RuntimeError('The runlevel should be at least warning when logging.')
        if not self._active:
            self.print_header()

        # Inform user about current location in the source code
        location = self._get_location()
        if location != self._last_used_location:
            self._last_used_location = location
            print >> self._file
            print >> self._file, ('<<< %s' % location).rjust(self.width)

        # Check for alignment code '&'
        pos = s.find(u'&')
        if pos == -1:
            lead = u''
            rest = s
        else:
            lead = s[:pos] + ' '
            rest = s[pos+1:]
        width = self.width - len(lead)
        if width < self.width/2:
            raise ValueError('The lead may not exceed half the width of the terminal.')

        # Break and print the line
        first = True
        while len(rest) > 0:
            if len(rest) > width:
                pos = rest.rfind(' ', 0, width)
                if pos == -1:
                    current = rest[:width]
                    rest = rest[width:]
                else:
                    current = rest[:pos]
                    rest = rest[pos:].lstrip()
            else:
                current = rest
                rest = u''
            print >> self._file, u'%s%s' % (lead, current)
            if first:
                lead = u' '*len(lead)
                first = False

    def warn(self, *words):
        text = u'WARNING!!&'+u' '.join(unicode(w) for w in words)
        text = '%s%s%s' % (self.red, text, self.reset)
        self(text)

    def hline(self, char='~'):
        print >> self._file, char*self.width

    def center(self, *words, **kwargs):
        if len(kwargs) == 0:
            edge = ''
        elif len(kwargs) == 1:
            if 'edge' not in kwargs:
                raise TypeError('Only one keyword argument is allowed, that is edge')
            edge = kwargs['edge']
        else:
            raise TypeError('Too many keyword arguments. Should be at most one.')
        s = u' '.join(unicode(w) for w in words)
        if len(s) + 2*len(edge) > self.width:
            raise ValueError('Line too long. center method does not support wrapping.')
        self('%s%s%s' % (edge, s.center(self.width-2*len(edge)), edge))

    def blank(self):
        print >> self._file

    def deflist(self, l):
        widest = max(len(item[0]) for item in l)
        for name, value in l:
            self('  %s :&%s' % (name.ljust(widest), value))

    def cite(self, key, reason):
        if self._biblio is None:
            filename = horton.context.get_fn('references.bib')
            self._biblio = Biblio(filename)
        self._biblio.cite(key, reason)

    def print_header(self):
        if self.do_warning and not self._active:
            self._active = True
            print >> self._file, self.head_banner
            self._print_basic_info()

    def print_footer(self):
        if self.do_warning and self._active:
            self._print_references()
            self._print_basic_info()
            self.timer._stop('Total')
            self.timer.report(self)
            print >> self._file, self.foot_banner

    def _get_location(self):
        tb = traceback.extract_stack()
        hit = False
        for row in tb[::-1]:
            in_log = row[0].endswith('horton/log.py')
            if in_log and row[2] == '__call__':
                if hit:
                    result = row[0]
                    break
                else:
                    hit = True
            elif hit and not in_log:
                result = row[0]
                break
        if 'horton/' not in result:
            result = tb[-1][0]
        result = result[result.find('horton/'):]
        return result

    def _print_references(self):
        if self._biblio is not None:
            self._biblio.log()

    def _print_basic_info(self):
        if self.do_low:
            self('User:          &' + getpass.getuser())
            self('Machine info:  &' + ' '.join(os.uname()))
            self('Time:          &' + datetime.datetime.now().isoformat())
            self('Python version:&' + sys.version.replace('\n', ''))
            self('%s&%s' % (('%s version:' % self.name).ljust(15), self.version))
            self('Current Dir:   &' + os.getcwd())
            self('Command line:  &' + ' '.join(sys.argv))
            self('Horton module: &' + __file__)


class Timer(object):
    def __init__(self):
        self.cpu = 0.0
        self._start = None

    def start(self):
        assert self._start is None
        self._start = time.clock()

    def stop(self):
        assert self._start is not None
        self.cpu += time.clock() - self._start
        self._start = None


class SubTimer(object):
    def __init__(self, label):
        self.label = label
        self.total = Timer()
        self.own = Timer()

    def start(self):
        self.total.start()
        self.own.start()

    def start_sub(self):
        self.own.stop()

    def stop_sub(self):
        self.own.start()

    def stop(self):
        self.own.stop()
        self.total.stop()


class TimerGroup(object):
    def __init__(self):
        self.parts = {}
        self._stack = []
        self._start('Total')

    def reset(self):
        for timer in self.parts.itervalues():
            timer.total.cpu = 0.0
            timer.own.cpu = 0.0

    @contextmanager
    def section(self, label):
        self._start(label)
        try:
            yield
        finally:
            self._stop(label)

    def _start(self, label):
        assert len(label) <= 14
        # get the right timer object
        timer = self.parts.get(label)
        if timer is None:
            timer = SubTimer(label)
            self.parts[label] = timer
        # start timing
        timer.start()
        if len(self._stack) > 0:
            self._stack[-1].start_sub()
        # put it on the stack
        self._stack.append(timer)

    def _stop(self, label):
        timer = self._stack.pop(-1)
        assert timer.label == label
        timer.stop()
        if len(self._stack) > 0:
            self._stack[-1].stop_sub()

    def get_max_own_cpu(self):
        result = None
        for part in self.parts.itervalues():
            if result is None or result < part.own.cpu:
                result = part.own.cpu
        return result

    def report(self, log):
        max_own_cpu = self.get_max_own_cpu()
        #if max_own_cpu == 0.0:
        #    return
        log.blank()
        log('Overview of CPU time usage.')
        log.hline()
        log('Label             Total      Own')
        log.hline()
        bar_width = log.width-33
        for label, timer in sorted(self.parts.iteritems()):
            #if timer.total.cpu == 0.0:
            #    continue
            if max_own_cpu > 0:
                cpu_bar = "W"*int(timer.own.cpu/max_own_cpu*bar_width)
            else:
                cpu_bar = ""
            log('%14s %8.1f %8.1f %s' % (
                label.ljust(14),
                timer.total.cpu, timer.own.cpu, cpu_bar.ljust(bar_width),
            ))
        log.hline()
        ru = resource.getrusage(resource.RUSAGE_SELF)
        log.deflist([
            ('CPU user time', '% 10.2f' % ru.ru_utime),
            ('CPU sysem time', '% 10.2f' % ru.ru_stime),
            ('Page swaps', '% 10i' % ru.ru_nswap),
        ])
        log.hline()


class Reference(object):
    def __init__(self, kind, key):
        self.kind = kind
        self.key = key
        self.tags = {}

    def format_str(self):
        if self.kind == 'article':
            if 'doi' in self.tags:
                url = ';http://dx.doi.org/%s' % self.tags['doi']
            else:
                url = ''
            return '%s; %s %s (v. %s pp. %s)%s' % (
                self.tags['author'].replace(' and', ';'), self.tags['journal'],
                self.tags['year'], self.tags['volume'], self.tags['pages'], url,
            )
        else:
            raise NotImplementedError


class Biblio(object):
    def __init__(self, filename):
        self.filename = filename
        self._records = {}
        self._cited = {}
        self._done = set([])
        self._load(filename)

    def _load(self, filename):
        with open(filename) as f:
            current = None
            for line in f:
                line = line[:line.find('%')].strip()
                if len(line) == 0:
                    continue
                if line.startswith('@'):
                    assert current is None
                    kind = line[line.find('@')+1:line.find('{')]
                    key = line[line.find('{')+1:line.find(',')]
                    current = Reference(kind, key)
                elif line == '}':
                    assert current is not None
                    self._records[current.key] = current
                    current = None
                elif current is not None:
                    tag = line[:line.find('=')].strip()
                    value = line[line.find('=')+1:].strip()
                    assert value[0] == '{'
                    assert value[-2:] == '},' or value[-1] == '}'
                    if value[-1] == '}':
                        value = value[1:-1]
                    else:
                        value = value[1:-2]
                    current.tags[tag] = value

    def cite(self, key, reason):
        if (key, reason) not in self._done:
            self._cited[key] = self._records[key]
            self._done.add((key, reason))
            if log.do_low:
                log('Please cite "%s" for %s.' % (key, reason))

    def log(self):
        if log.do_low:
            log('The following references were cited:')
            log.hline()
            log.deflist([
                (key, reference.format_str()) for key, reference
                in sorted(self._cited.iteritems())
            ])
            log.hline()
            log('Details can be found in the file %s' % self.filename)
            log.blank()


class MemoryLogger(object):
    def __init__(self, log):
        self._big = 0
        self.log = log

    def announce(self, amount):
        unit = float(1024*1024)
        if self.log.do_high:
            self.log('Will allocate: %.1f MB. Current: %.1f MB. RSS: %.1f MB' %(
                amount/unit, self._big/unit, self.get_rss()/unit
            ))
            self._big += amount
        if self.log.do_debug:
            traceback.print_stack()
            self.log.blank()

    def denounce(self, amount):
        unit = float(1024*1024)
        if self.log.do_high:
            self.log('Will release:  %.1f MB. Current: %.1f MB. RSS: %.1f MB' %(
                amount/unit, self._big/unit, self.get_rss()/unit
            ))
            self._big -= amount
        if self.log.do_debug:
            traceback.print_stack()
            self.log.blank()

    def get_rss(self):
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*resource.getpagesize()


head_banner = """\
 _ __ _
/ (..) \ Welcome to Horton, an open source constrained HF/DFT/1RDM program.
\/ || \/
 |_''_|  Horton is written by Toon Verstraelen (1) and Matthew Chan (2).

         (1) Center for Molecular Modeling, Ghent University, Belgium.
         (2) The Ayers Group at McMaster University, Ontario, Canada.

         More information about Horton can be found on this website:
         http://theochem.github.com/horton/

         The purpose of this log file is to track the progress and quality of a
         computation. Useful numerical output may be written to a checkpoint
         file and is accessible through the Python scripting interface.

================================================================================"""


foot_banner = """
================================================================================
 _    _
/ )--( \ End of the Horton program.
\|  \ |/
 |_||_|  Thank you for using Horton! See you soon!
"""

timer = TimerGroup()
log = ScreenLog('HORTON', horton.__version__, head_banner, foot_banner, timer)
# TODO: avoid printing footer in case of exception
atexit.register(log.print_footer)
