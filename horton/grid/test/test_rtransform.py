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


import numpy as np

from horton import *



def check_consistency(rtf):
    ts = np.random.uniform(0, rtf.npoint-1, 200)
    # consistency between radius and radius_array
    rs = np.zeros(ts.shape)
    rtf.radius_array(ts, rs)
    for i in xrange(ts.shape[0]):
        assert rs[i] == rtf.radius(ts[i])
    # consistency between deriv and deriv_array
    ds = np.zeros(ts.shape)
    rtf.deriv_array(ts, ds)
    for i in xrange(ts.shape[0]):
        assert ds[i] == rtf.deriv(ts[i])
    # consistency between inv and inv_array
    ts[:] = 0.0
    rtf.inv_array(rs, ts)
    for i in xrange(ts.shape[0]):
        assert ts[i] == rtf.inv(rs[i])
    # consistency between inv and radius
    for i in xrange(ts.shape[0]):
        assert abs(ts[i] - rtf.inv(rtf.radius(ts[i]))) < 1e-10

    ts = np.arange(rtf.npoint, dtype=float)
    # consistency of get_radii
    radii = rtf.get_radii()
    assert radii.shape == (rtf.npoint,)
    rs = np.zeros(ts.shape)
    rtf.radius_array(ts, rs)
    assert (rs == radii).all()
    # consistency of get_volume_elements
    volume_elements = rtf.get_volume_elements()
    assert volume_elements.shape == (rtf.npoint,)
    ds = np.zeros(ts.shape)
    rtf.deriv_array(ts, ds)
    assert (ds == volume_elements).all()
    # radii must increase strictly
    assert (radii[1:] > radii[:-1]).all()


def check_deriv(rtf):
    ts = np.random.uniform(0, rtf.npoint-1, 200)
    eps = 1e-5
    ts0 = ts-eps/2
    ts1 = ts+eps/2
    rs0 = np.zeros(ts.shape)
    rtf.radius_array(ts0, rs0)
    rs1 = np.zeros(ts.shape)
    rtf.radius_array(ts1, rs1)
    ds = np.zeros(ts.shape)
    rtf.deriv_array(ts, ds)
    dns = (rs1-rs0)/eps
    assert abs(ds-dns).max() < 1e-8


def check_chop(rtf1):
    assert rtf1.npoint == 100
    rtf2 = rtf1.chop(50)
    assert rtf1.__class__ == rtf2.__class__
    assert rtf2.npoint == 50
    assert abs(rtf1.get_radii()[:50] - rtf2.get_radii()).max() < 1e-8


def test_identity_basics():
    rtf = IdentityRTransform(100)
    assert rtf.radius(0.0) == 0.0
    assert rtf.radius(99.0) == 99.0
    check_consistency(rtf)
    check_deriv(rtf)
    check_chop(rtf)


def test_linear_basics():
    rtf = LinearRTransform(-0.7, 0.8, 100)
    assert abs(rtf.radius(0) - -0.7) < 1e-15
    assert abs(rtf.radius(99) - 0.8) < 1e-10
    check_consistency(rtf)
    check_deriv(rtf)
    check_chop(rtf)


def test_exp_basics():
    rtf = ExpRTransform(0.1, 1e1, 100)
    assert abs(rtf.radius(0) - 0.1) < 1e-15
    assert abs(rtf.radius(99) - 1e1) < 1e-10
    check_consistency(rtf)
    check_deriv(rtf)
    check_chop(rtf)


def test_shifted_exp_basics():
    rtf = ShiftedExpRTransform(0.1, 0.1, 10.0, 100)
    assert abs(rtf.radius(0) - 0.1) < 1e-15
    assert abs(rtf.radius(99) - 10.0) < 1e-10
    check_consistency(rtf)
    check_deriv(rtf)
    check_chop(rtf)


def test_baker_basics():
    rtf = BakerRTransform(1e1, 100)
    assert rtf.radius(0) > 0.0
    assert abs(rtf.radius(99) - 1e1) < 1e-10
    check_consistency(rtf)
    check_deriv(rtf)


def test_identity_properties():
    rtf = IdentityRTransform(100)
    assert rtf.npoint == 100


def test_linear_properties():
    rtf = LinearRTransform(-0.7, 0.8, 100)
    assert rtf.rmin == -0.7
    assert rtf.rmax == 0.8
    assert rtf.npoint == 100
    assert rtf.alpha > 0


def test_exp_properties():
    rtf = ExpRTransform(0.1, 1e1, 100)
    assert rtf.rmin == 0.1
    assert rtf.rmax == 1e1
    assert rtf.npoint == 100
    assert rtf.alpha > 0


def test_shifted_exp_properties():
    rtf = ShiftedExpRTransform(0.2, 0.1, 1e1, 100)
    assert rtf.rmin == 0.2
    assert rtf.rshift == 0.1
    assert rtf.rmax == 1e1
    assert rtf.npoint == 100
    assert abs(rtf.r0 - 0.3) < 1e-10
    assert rtf.alpha > 0


def test_baker_properties():
    rtf = BakerRTransform(1e1, 100)
    assert rtf.rmax == 1e1
    assert rtf.npoint == 100
    assert rtf.scale < 0


def test_exception_string():
    try:
        RTransform.from_string('Fubar A 5')
        assert False
    except TypeError:
        pass


def test_identiy_string():
    rtf1 = IdentityRTransform(45)
    s = rtf1.to_string()
    rtf2 = RTransform.from_string(s)
    assert rtf1.npoint == rtf2.npoint

    try:
        rtf3 = RTransform.from_string('IdentityRTransform A')
        assert False
    except ValueError:
        pass

    try:
        rtf3 = RTransform.from_string('IdentityRTransform A 5 .1')
        assert False
    except ValueError:
        pass

    rtf3 = RTransform.from_string('IdentityRTransform 8')
    assert rtf3.npoint == 8



def test_linear_string():
    rtf1 = LinearRTransform(np.random.uniform(1e-5, 5e-5), np.random.uniform(1, 5), 88)
    s = rtf1.to_string()
    rtf2 = RTransform.from_string(s)
    assert rtf1.rmin == rtf2.rmin
    assert rtf1.rmax == rtf2.rmax
    assert rtf1.npoint == rtf2.npoint
    assert rtf1.alpha == rtf2.alpha

    try:
        rtf3 = RTransform.from_string('LinearRTransform A 5')
        assert False
    except ValueError:
        pass

    try:
        rtf3 = RTransform.from_string('LinearRTransform A 5 .1')
        assert False
    except ValueError:
        pass

    rtf3 = RTransform.from_string('LinearRTransform -1.0 12.15643216847 77')
    assert rtf3.rmin == -1.0
    assert rtf3.rmax == 12.15643216847
    assert rtf3.npoint == 77
    assert rtf3.alpha > 0


def test_exp_string():
    rtf1 = ExpRTransform(np.random.uniform(1e-5, 5e-5), np.random.uniform(1, 5), 111)
    s = rtf1.to_string()
    rtf2 = RTransform.from_string(s)
    assert rtf1.rmin == rtf2.rmin
    assert rtf1.rmax == rtf2.rmax
    assert rtf1.npoint == rtf2.npoint
    assert rtf1.alpha == rtf2.alpha

    try:
        rtf3 = RTransform.from_string('ExpRTransform A 5')
        assert False
    except ValueError:
        pass

    try:
        rtf3 = RTransform.from_string('ExpRTransform A 5 .1')
        assert False
    except ValueError:
        pass

    rtf3 = RTransform.from_string('ExpRTransform 1.0 12.15643216847 5')
    assert rtf3.rmin == 1.0
    assert rtf3.rmax == 12.15643216847
    assert rtf3.npoint == 5
    assert rtf3.alpha > 0


def test_shifted_exp_string():
    rtf1 = ShiftedExpRTransform(np.random.uniform(1e-4, 5e-4), np.random.uniform(1e-5, 5e-5), np.random.uniform(1, 5), 781)
    s = rtf1.to_string()
    rtf2 = RTransform.from_string(s)
    assert rtf1.rmin == rtf2.rmin
    assert rtf1.rshift == rtf2.rshift
    assert rtf1.rmax == rtf2.rmax
    assert rtf1.npoint == rtf2.npoint
    assert rtf1.r0 == rtf2.r0
    assert rtf1.alpha == rtf2.alpha

    try:
        rtf3 = RTransform.from_string('ShiftedExpRTransform A 5')
        assert False
    except ValueError:
        pass

    try:
        rtf3 = RTransform.from_string('ShiftedExpRTransform A 5 .1 14')
        assert False
    except ValueError:
        pass

    rtf3 = RTransform.from_string('ShiftedExpRTransform 1.0 0.5 12.15643216847 5')
    assert rtf3.rmin == 1.0
    assert rtf3.rshift == 0.5
    assert rtf3.rmax == 12.15643216847
    assert rtf3.npoint == 5
    assert rtf3.alpha > 0


def test_baker_string():
    rtf1 = BakerRTransform(np.random.uniform(1, 5), 123)
    s = rtf1.to_string()
    rtf2 = RTransform.from_string(s)
    assert rtf1.rmax == rtf2.rmax
    assert rtf1.npoint == rtf2.npoint
    assert rtf1.scale == rtf2.scale

    try:
        rtf3 = RTransform.from_string('BakerRTransform A 5 7')
        assert False
    except ValueError:
        pass

    try:
        rtf3 = RTransform.from_string('ExpRTransform A 5.0')
        assert False
    except ValueError:
        pass

    rtf3 = RTransform.from_string('BakerRTransform 12.15643216847 5')
    assert rtf3.rmax == 12.15643216847
    assert rtf3.npoint == 5
    assert rtf3.scale < 0


def test_identity_bounds():
    for npoint in -1, 0, 1:
        try:
            IdentityRTransform(npoint)
            assert False
        except ValueError:
            pass


def test_linear_bounds():
    for npoint in -1, 0, 1:
        try:
            LinearRTransform(-0.5, 0.99, npoint)
            assert False
        except ValueError:
            pass

    try:
        LinearRTransform(1.1, 0.9, 50)
        assert False
    except ValueError:
        pass


def test_exp_bounds():
    for npoint in -1, 0, 1:
        try:
            ExpRTransform(0.1, 1.0, npoint)
            assert False
        except ValueError:
            pass

    try:
        ExpRTransform(-0.1, 1.0, 50)
        assert False
    except ValueError:
        pass

    try:
        ExpRTransform(0.1, -1.0, 50)
        assert False
    except ValueError:
        pass

    try:
        ExpRTransform(1.1, 0.9, 50)
        assert False
    except ValueError:
        pass


def test_shifted_exp_bounds():
    for npoint in -1, 0, 1:
        try:
            ShiftedExpRTransform(0.1, 0.05, 1.0, npoint)
            assert False
        except ValueError:
            pass

    try:
        ShiftedExpRTransform(-0.1, 0.2, 1.0, 50)
        assert False
    except ValueError:
        pass

    try:
        ShiftedExpRTransform(0.1, 0.2, -1.0, 50)
        assert False
    except ValueError:
        pass

    try:
        ShiftedExpRTransform(1.1, 0.2, 0.9, 50)
        assert False
    except ValueError:
        pass

    try:
        ShiftedExpRTransform(0.1, -0.3, 0.9, 50)
        assert False
    except ValueError:
        pass


def test_baker_bounds():
    for npoint in -1, 0, 1:
        try:
            BakerRTransform(1.0, npoint)
            assert False
        except ValueError:
            pass

    try:
        BakerRTransform(-1.0, 50)
        assert False
    except ValueError:
        pass
