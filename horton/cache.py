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
'''Tools for avoiding recomputation of earlier results and reallocation of
   existing arrays.

   In principle, the ``JustOnceClass`` and the ``Cache`` can be used
   independently, but in some cases it makes a lot of sense to combine them.
   See for example the density partitioning code in ``horton.part``.
'''


import numpy as np, h5py as h5, os
from horton.log import log

from horton.matrix import LinalgObject


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

       When all results are outdated, one can call the ``clear`` method
       to forget which methods were called already.
    '''
    def __init__(self):
        self._done_just_once = set([])

    def __clear__(self):
        self.clear()

    def clear(self):
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
            elif alloc[1] == 'two_body':
                return cls(alloc[0].create_two_body(*alloc[2:]))
            elif alloc[1] == 'expansion':
                return cls(alloc[0].create_expansion(*alloc[2:]))
            else:
                raise TypeError('Not supported: %s.' % alloc[1])
        else:
            # initialize a floating point array
            array = np.zeros(alloc, float)
            log.mem.announce(array.nbytes)
            return cls(array, own=True)

    def __del__(self):
        if self._own and log is not None:
            assert isinstance(self._value, np.ndarray)
            log.mem.denounce(self._value.nbytes)

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
            elif alloc[1] == 'two_body':
                if not (len(alloc) == 2 or (len(alloc) == 3 and alloc[2] == self._value.nbasis)):
                    raise TypeError('The requested two-body operator is not compatible with the cached one.')
            elif alloc[1] == 'expansion':
                if not (len(alloc) == 2 or (len(alloc) == 3 and alloc[2] == self._value.nbasis) or
                        (len(alloc) == 4 and alloc[2] == self._value.nbasis and alloc[3] == self._value.nfn)):
                    raise TypeError('The requested expansion is not compatible with the cached one.')
            else:
                raise TypeError('Not supported: %s.' % alloc[1])
        else:
            # assume a floating point array
            if not (isinstance(self._value, np.ndarray) and
                    self._value.shape == tuple(alloc) and
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

    def _get_clearable(self):
        return isinstance(self._value, np.ndarray) or \
               (hasattr(self._value, '__clear__') and callable(self._value.__clear__))

    clearable = property(_get_clearable)

    def clear(self):
        '''Mark the item as invalid and clear the contents of the object.'''
        self._valid = False
        if isinstance(self._value, np.ndarray):
            self._value[:] = 0.0
        elif hasattr(self._value, '__clear__') and callable(self._value.__clear__):
            self._value.__clear__()
        else:
            raise TypeError('Do not know how to clear %s.' % self._value)


class NoDefault(object):
    pass


no_default = NoDefault()


def normalize_key(key):
    if hasattr(key, '__len__') and  len(key) == 0:
        raise TypeError('At least one argument needed to specify a key.')
    # upack the key if needed
    while len(key) == 1 and isinstance(key, tuple):
        key = key[0]
    return key


class Cache(object):
    '''Object that stores previously computed results.

       The cache behaves like a dictionary with some extra features that can be
       used to avoid recomputation or reallocation.
    '''
    def __init__(self):
        self._store = {}

    def clear(self, dealloc=False):
        '''Clear all items in the cache

           **Optional arguments:**

           dealloc
                When set to True, the items are really removed from memory.
        '''
        for key in self._store.keys():
            self.clear_item(key, dealloc=dealloc)

    def clear_item(self, *key, **kwargs):
        '''Clear a selected item from the cache

           **Optional arguments:**

           dealloc
                When set to True, the item is really removed from memory.
        '''
        key = normalize_key(key)
        dealloc = kwargs.pop('dealloc', False)
        if len(kwargs) > 0:
            raise TypeError('Unexpected arguments: %s' % kwargs.keys())
        item = self._store.get(key)
        if item is None:
            return
        if item.clearable and not dealloc:
            item.clear()
        else:
            del self._store[key]

    # TODO: the alloc argument is just too ugly to be useful. (Add this to
    # Trello in the card with the new classes for the matrix module.)
    def load(self, *key, **kwargs):
        '''Get a value from the cache

           **Arguments:**

           key0 [key1 ...]
                All positional arguments are used as keys to identify the cached
                value.

           **Optional arguments:** (at most one is accepted)

           alloc
                Parameters used to allocated a cached value if it is not present
                yet. This argument can take several forms. When integer or a
                tuple of integers is given, an array is allocated.
                Alternatively, a tuple may be given whose first element is a
                linalg factory, the second is 'expansion', 'one_body' or
                'two_body'. Further (optional) elements correspond to arguments
                of the corresponding create_* methods of the linalg factory
                object.

           default
                A default value that is returned when the key does not exist in
                the cache. This default value is not stored in the cache.
        '''
        key = normalize_key(key)

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

        # get the item from the store and decide what to do
        item = self._store.get(key)
        # there are three behaviors, depending on the keyword argumentsL
        if alloc is not None:
            # alloc is given. hence two return values: value, new
            if item is None:
                # allocate a new item, s
                item = CacheItem.from_alloc(alloc)
                self._store[key] = item
                return item.value, True
            elif not item.valid:
                item.check_alloc(alloc)
                item._valid = True # as if it is newly allocated
                return item.value, True
            else:
                item.check_alloc(alloc)
                return item.value, False
        elif default is not no_default:
            # a default value is given, it is not stored
            if item is None or not item.valid:
                return default
            else:
                return item.value
        else:
            # no optional arguments are given
            if item is None or not item.valid:
                raise KeyError(key)
            else:
                return item.value

    def __contains__(self, key):
        key = normalize_key(key)
        item = self._store.get(key)
        if item is None:
            return False
        else:
            return item.valid

    def dump(self, *args, **kwargs):
        '''Store an object in the cache.

           **Arguments:**

           key1 [, key2, ...]
                The positional arguments (except for the last) are used as a key
                for the object.

           value
                The object to be stored.

           **Optional argument:**

           own
                When set to True, the cache will take care of denouncing the
                memory usage due to this array.
        '''
        own = kwargs.pop('own', False)
        if len(kwargs) > 0:
            raise TypeError('Unknown optional arguments: %s' % kwargs.keys())
        if len(args) < 2:
            raise TypeError('At least two arguments are required: key1 and value.')
        key = normalize_key(args[:-1])
        value = args[-1]
        item = CacheItem(value, own)
        self._store[key] = item

    def __len__(self):
        return sum(item.valid for item in self._store.itervalues())

    def __getitem__(self, key):
        return self.load(key)

    def __setitem__(self, key, value):
        return self.dump(key, value)

    def __iter__(self):
        return self.iterkeys()

    def iterkeys(self):
        '''Iterate over the keys of all valid items in the cache.'''
        for key, item in self._store.iteritems():
            if item.valid:
                yield key

    def itervalues(self):
        '''Iterate over the values of all valid items in the cache.'''
        for item in self._store.itervalues():
            if item.valid:
                yield item.value

    def iteritems(self):
        '''Iterate over all valid items in the cache.'''
        for key, item in self._store.iteritems():
            if item.valid:
                yield key, item.value
