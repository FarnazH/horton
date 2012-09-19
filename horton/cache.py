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
'''Tools for avoiding recomputation and reallocation of earlier results

   In principle, the ``JustOnceClass`` and the ``Cache`` can be used
   independently, but in some cases it makes a lot of sense to combine them.
   See for example. the density partitioning code in ``horton.dpart``.
'''


import numpy as np
from horton.log import log


__all__ = ['JustOnceClass', 'just_once', 'Cache']


class JustOnceClass(object):
    '''Base class for classes with methods that should never be executed twice.

       In typically applications, these methods get called many times, but
       only during the first call, an actual computation is carried out. This
       way, the caller can safely call a method, just to make sure that a
       required result is computed.

       All methods in the subclasses that should have this feature, must be
       given the ``just_once`` decoratore, e.g. ::

           class Example(JustOnceClass):
               @just_once
               def do_something():
                   self.foo = self.bar

       When all results are outdate, one can call the ``invalidate`` method
       to forget which methods were called already.
    '''
    def __init__(self):
        self._done_just_once = set([])

    def invalidate(self):
        self._done_just_once = set([])


def just_once(fn):
    def wrapper(instance):
        if not hasattr(instance, '_done_just_once'):
            raise TypeError('Missing hidden _done_just_once. Forgot to call JustOnceClass.__init__()?')
        if fn.func_name in instance._done_just_once:
            return
        fn(instance)
        instance._done_just_once.add(fn.func_name)
    wrapper.__doc__ = fn.__doc__
    return wrapper



class CacheItem(object):
    def __init__(self, value, own=False):
        self._value = value
        self._valid = True
        self._own = own

    @classmethod
    def from_alloc(cls, alloc):
        from horton.matrix import LinalgFactory
        if not hasattr(alloc, '__len__'):
            alloc = (alloc,)
        if isinstance(alloc[0], LinalgFactory):
            if len(alloc) < 2:
                raise TypeError('Add least one extra parameter needed to initialize a linalg thing')
            if alloc[1] == 'one_body':
                return cls(alloc[0].create_one_body(*alloc[2:]))
            else:
                raise TypeError('For the moment, only one_body stuff is supported.')
        else:
            # initialize a floating point array
            log.mem.announce(np.product(alloc)*8)
            return cls(np.zeros(alloc, float), own=True)

    def __del__(self):
        if self._own:
            assert isinstance(self._value, np.ndarray)
            log.mem.denounce(self._value.size*8)

    def check_alloc(self, alloc):
        from horton.matrix import LinalgFactory
        if not hasattr(alloc, '__len__'):
            alloc = (alloc,)
        if isinstance(alloc[0], LinalgFactory):
            if len(alloc) < 2:
                raise TypeError('Add least one extra parameter needed to initialize a linalg thing')
            if alloc[1] == 'one_body':
                if not (len(alloc) == 2 or (len(alloc) == 3 and alloc[2] == self._value.nbasis)):
                    raise TypeError('The requested one-body operator is not compatible with the cached one.')
            else:
                raise TypeError('For the moment, only one_body stuff is supported.')
        else:
            # assume a floating point array
            if not (isinstance(self._value, np.ndarray) and
                    self._value.shape == alloc and
                    issubclass(self._value.dtype.type, float)):
                raise TypeError('The stored item does not match the given alloc.')

    def _get_value(self):
        if not self._valid:
            raise ValueError('This cached item is not valid.')
        return self._value

    value = property(_get_value)

    def _get_valid(self):
        return self._valid

    valid = property(_get_valid)

    def _get_resettable(self):
        from horton.matrix import OneBody
        return isinstance(self._value, np.ndarray) or \
               isinstance(self._value, OneBody)

    resettable = property(_get_resettable)

    def invalidate(self):
        self._valid = False
        self.reset()

    def reset(self):
        from horton.matrix import OneBody
        if isinstance(self._value, np.ndarray):
            self._value[:] = 0.0
        elif isinstance(self._value, OneBody):
            self._value.reset()
        else:
            raise TypeError('Do not know how to reset %s.' % self._value)


class NoDefault(object):
    pass


no_default = NoDefault()


class Cache(object):
    '''Object that stores previously computed results.

       This is geared towards storing numerical results. The load method
       may be used to initialize new floating point arrays if they are not
       cached yet.
    '''
    def __init__(self):
        self._store = {}

    def invalidate(self):
        for key in self._store.keys():
            item = self._store[key]
            if item.resettable:
                # avoid re-allocation
                item.invalidate()
            else:
                del self._store[key]

    def load(self, *key, **kwargs):
        # check key
        if len(key) == 0:
            raise TypeError('At least one non-keyword argument is required')

        # parse kwargs
        if len(kwargs) == 0:
            alloc = None
            default = no_default
        elif len(kwargs) == 1:
            name, value = kwargs.items()[0]
            if name == 'alloc':
                alloc = value
                default = no_default
            elif name == 'default':
                alloc = None
                default = value
            else:
                raise TypeError('Only one keyword argument is allowed: alloc or default')
        else:
            raise TypeError('Only one keyword argument is allowed: alloc or default')

        item = self._store.get(key)
        if item is None:
            if alloc is None and default is no_default:
                raise KeyError('Could not find item %s' % repr(key))
            elif default is no_default:
                item = CacheItem.from_alloc(alloc)
                self._store[key] = item
                return item.value, True
            else:
                return default
        if alloc is None:
            if item.valid:
                return item.value
            else:
                raise KeyError('Item %s is not valid.' % repr(key))
        else:
            item.check_alloc(alloc)
            new = not item.valid
            item._valid = True # as if it is newly allocated
            return item.value, new

    def has(self, *key):
        item = self._store.get(key)
        if item is None:
            return False
        else:
            return item.valid

    def dump(self, *args):
        if len(args) < 2:
            raise TypeError('At least two arguments are required: key1 and value.')
        key = args[:-1]
        value = args[-1]
        item = CacheItem(value)
        self._store[key] = item

    def discard(self, *key):
        '''Genuinly discards a cached item from the store, no sneaky reset.'''
        if key in self._store:
            del self._store[key]
