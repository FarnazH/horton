// Horton is a Density Functional Theory program.
// Copyright (C) 2011-2013 Toon Verstraelen <Toon.Verstraelen@UGent.be>
//
// This file is part of Horton.
//
// Horton is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 3
// of the License, or (at your option) any later version.
//
// Horton is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, see <http://www.gnu.org/licenses/>
//
//--


//#define DEBUG

#ifdef DEBUG
#include <cstdio>
#endif

#include <cmath>
#include <stdexcept>
#include "cell.h"


void Cell::update(double* _rvecs, double* _gvecs, int _nvec) {
    // just copy everything
    nvec = _nvec;
    for (int i=8; i>=0; i--) {
        rvecs[i] = _rvecs[i];
        gvecs[i] = _gvecs[i];
    }
    // compute the spacings
    for (int i=2; i>=0; i--) {
        rspacings[i] = 1.0/sqrt(gvecs[3*i]*gvecs[3*i] + gvecs[3*i+1]*gvecs[3*i+1] + gvecs[3*i+2]*gvecs[3*i+2]);
        gspacings[i] = 1.0/sqrt(rvecs[3*i]*rvecs[3*i] + rvecs[3*i+1]*rvecs[3*i+1] + rvecs[3*i+2]*rvecs[3*i+2]);
    }
    // compute the volume
    switch(nvec) {
        case 0:
            volume = 0.0;
            break;
        case 1:
            volume = sqrt(
                rvecs[0]*rvecs[0]+rvecs[1]*rvecs[1]+rvecs[2]*rvecs[2]
            );
            break;
        case 2:
            double tmp;
            tmp = rvecs[0]*rvecs[3]+rvecs[1]*rvecs[4]+rvecs[2]*rvecs[5];
            tmp = (rvecs[0]*rvecs[0]+rvecs[1]*rvecs[1]+rvecs[2]*rvecs[2])*
                  (rvecs[3]*rvecs[3]+rvecs[4]*rvecs[4]+rvecs[5]*rvecs[5]) - tmp*tmp;
            if (tmp > 0) {
                volume = sqrt(tmp);
            } else {
                volume = 0.0;
            }
            break;
        case 3:
            volume = fabs(
                rvecs[0]*(rvecs[4]*rvecs[8]-rvecs[5]*rvecs[7])+
                rvecs[1]*(rvecs[5]*rvecs[6]-rvecs[3]*rvecs[8])+
                rvecs[2]*(rvecs[3]*rvecs[7]-rvecs[4]*rvecs[6])
            );
            break;
  }
}


double Cell::get_rspacing(int i) {
    if ((i < 0) || (i > 3)) {
        throw std::domain_error("Index must be 0, 1 or 2.");
    }
    return rspacings[i];
}


double Cell::get_gspacing(int i) {
    if ((i < 0) || (i > 3)) {
        throw std::domain_error("Index must be 0, 1 or 2.");
    }
    return gspacings[i];
}


void Cell::mic(double* delta) {
    // Applies the Minimum Image Convention. Well, sort of. It does not always work like this.
    // This function contains an unrolled loop for speed.
    double x;
    if (nvec == 0) return;
    x = ceil(gvecs[0]*delta[0] + gvecs[1]*delta[1] + gvecs[2]*delta[2] - 0.5);
    delta[0] -= x*rvecs[0];
    delta[1] -= x*rvecs[1];
    delta[2] -= x*rvecs[2];
    if (nvec == 1) return;
    x = ceil(gvecs[3]*delta[0] + gvecs[4]*delta[1] + gvecs[5]*delta[2] - 0.5);
    delta[0] -= x*rvecs[3];
    delta[1] -= x*rvecs[4];
    delta[2] -= x*rvecs[5];
    if (nvec == 2) return;
    x = ceil(gvecs[6]*delta[0] + gvecs[7]*delta[1] + gvecs[8]*delta[2] - 0.5);
    delta[0] -= x*rvecs[6];
    delta[1] -= x*rvecs[7];
    delta[2] -= x*rvecs[8];
}


void Cell::to_center(double* cart, long* center) {
    // Transfroms to fractional coordinates
    if (nvec == 0) return;
    center[0] = -ceil(gvecs[0]*cart[0] + gvecs[1]*cart[1] + gvecs[2]*cart[2] - 0.5);
    if (nvec == 1) return;
    center[1] = -ceil(gvecs[3]*cart[0] + gvecs[4]*cart[1] + gvecs[5]*cart[2] - 0.5);
    if (nvec == 2) return;
    center[2] = -ceil(gvecs[6]*cart[0] + gvecs[7]*cart[1] + gvecs[8]*cart[2] - 0.5);
}


void Cell::to_frac(double* cart, double* frac) {
    // Transfroms to fractional coordinates
    frac[0] = gvecs[0]*cart[0] + gvecs[1]*cart[1] + gvecs[2]*cart[2];
    frac[1] = gvecs[3]*cart[0] + gvecs[4]*cart[1] + gvecs[5]*cart[2];
    frac[2] = gvecs[6]*cart[0] + gvecs[7]*cart[1] + gvecs[8]*cart[2];
}

void Cell::to_cart(double* frac, double* cart) {
    // Transfroms to Cartesian coordinates
    cart[0] = rvecs[0]*frac[0] + rvecs[3]*frac[1] + rvecs[6]*frac[2];
    cart[1] = rvecs[1]*frac[0] + rvecs[4]*frac[1] + rvecs[7]*frac[2];
    cart[2] = rvecs[2]*frac[0] + rvecs[5]*frac[1] + rvecs[8]*frac[2];
}


void Cell::add_vec(double* delta, long* r) {
    // Simply adds an linear combination of cell vectors to delta.
    // This function contains an unrolled loop for speed.
    if (nvec == 0) return;
    delta[0] += r[0]*rvecs[0];
    delta[1] += r[0]*rvecs[1];
    delta[2] += r[0]*rvecs[2];
    if (nvec == 1) return;
    delta[0] += r[1]*rvecs[3];
    delta[1] += r[1]*rvecs[4];
    delta[2] += r[1]*rvecs[5];
    if (nvec == 2) return;
    delta[0] += r[2]*rvecs[6];
    delta[1] += r[2]*rvecs[7];
    delta[2] += r[2]*rvecs[8];
}


void Cell::copy_rvecs(double* _rvecs) {
    for (int i=nvec*3-1; i>=0; i--) _rvecs[i] = rvecs[i];
}


void Cell::copy_gvecs(double* _gvecs) {
    for (int i=nvec*3-1; i>=0; i--) _gvecs[i] = gvecs[i];
}


void Cell::copy_rspacings(double* _rspacings) {
    for (int i=nvec-1; i>=0; i--) _rspacings[i] = rspacings[i];
}


void Cell::copy_gspacings(double* _gspacings) {
    for (int i=nvec-1; i>=0; i--) _gspacings[i] = gspacings[i];
}


void Cell::set_ranges_rcut(double* origin, double* center, double rcut,
                           long* ranges_begin, long* ranges_end) {
    double delta[3];
    delta[0] = center[0] - origin[0];
    delta[1] = center[1] - origin[1];
    delta[2] = center[2] - origin[2];
    double frac[3];
    to_frac(delta, frac);

    for (int i=nvec-1; i>=0; i--) {
        double step = rcut/rspacings[i];
        ranges_begin[i] = ceil(frac[i]-step);
        ranges_end[i] = ceil(frac[i]+step);
    }
}


long Cell::select_inside(double* origin, double* center, double rcut,
    long* ranges_begin, long* ranges_end, long* shape, long* pbc_active,
    long* indexes) {

    if (nvec == 0)
        throw std::domain_error("The cell must be at least 1D periodic for select_inside.");

    long my_ranges_begin[3];
    long my_ranges_end[3];
    long my_pbc_active[3];
    long my_shape[3];

    for (int i=nvec-1; i>=0; i--) {
        my_ranges_begin[i] = ranges_begin[i];
        my_ranges_end[i] = ranges_end[i];
        my_shape[i] = shape[i];
        my_pbc_active[i] = pbc_active[i];
    }
    for (int i=nvec; i<3; i++) {
        my_ranges_begin[i] = 0;
        my_ranges_end[i] = 1;
        my_shape[i] = 1;
        my_pbc_active[i] = 0;
    }

    long nselect = 0;

#ifdef DEBUG
    printf("my_ranges_begin={%li,%li,%li}\n", my_ranges_begin[0], my_ranges_begin[1], my_ranges_begin[2]);
    printf("my_ranges_end={%li,%li,%li}\n", my_ranges_end[0], my_ranges_end[1], my_ranges_end[2]);
    printf("my_shape={%li,%li,%li}\n", my_shape[0], my_shape[1], my_shape[2]);
    printf("my_pbc_active={%li,%li,%li}\n", my_pbc_active[0], my_pbc_active[1], my_pbc_active[2]);
#endif

    for (long i0 = my_ranges_begin[0]; i0 < my_ranges_end[0]; i0++) {
        long j0 = smart_wrap(i0, my_shape[0], my_pbc_active[0]);
        if (j0 == -1) continue;

        for (long i1 = my_ranges_begin[1]; i1 < my_ranges_end[1]; i1++) {
            long j1 = smart_wrap(i1, my_shape[1], my_pbc_active[1]);
            if (j1 == -1) continue;

            for (long i2 = my_ranges_begin[2]; i2 < my_ranges_end[2]; i2++) {
                long j2 = smart_wrap(i2, my_shape[2], my_pbc_active[2]);
                if (j2 == -1) continue;

                // Compute the distance between the point and the image of the center
                double frac[3], cart[3];
                frac[0] = i0;
                frac[1] = i1;
                frac[2] = i2;
                to_cart(frac, cart);
                double x = cart[0] + origin[0] - center[0];
                double y = cart[1] + origin[1] - center[1];
                double z = cart[2] + origin[2] - center[2];
                double d = sqrt(x*x+y*y+z*z);

                // if the distance is below rcut add this grid point.
                if (d < rcut) {
#ifdef DEBUG
                    printf("i={%li,%li,%li} j={%li,%li,%li} d=%e rcut=%e\n", i0, i1, i2, j0, j1, j2, d, rcut);
#endif
                    indexes[0] = j0;
                    if (nvec > 1) indexes[1] = j1;
                    if (nvec > 2) indexes[2] = j2;
                    indexes += nvec;
                    nselect++;
                }
            }
        }
    }

    return nselect;
}


long smart_wrap(long i, long shape, long pbc_active) {
    if ((i < 0) || (i >= shape)) {
        if (pbc_active) {
            long j = i%shape;
            if (j < 0) j += shape; // just to make sure that this works on all c++ compilers.
            return j;
        } else {
            return -1;
        }
    }
    return i;
}
