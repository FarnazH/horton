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


#ifndef HORTON_GBASIS_COMMON_H
#define HORTON_GBASIS_COMMON_H

#define MAX_SHELL_TYPE 7

// Simple math stuff
long fac(long n);
long fac2(long n);
long binom(long n, long m);
long get_shell_nbasis(long shell_type);
long get_max_shell_type();
const double dist_sq(const double* r0, const double* r1);

// Auxiliary functions for Gaussian integrals
void compute_gpt_center(double alpha0, const double* r0, double alpha1, const double* r1, double gamma_inv, double* gpt_center);
double gpt_coeff(long k, long n0, long n1, double pa, double pb);
double gb_overlap_int1d(long n0, long n1, double pa, double pb, double gamma_inv);
void nuclear_attraction_helper(double* work_g, long n0, long n1, double pa, double pb, double pc, double gamma_inv);

#endif
