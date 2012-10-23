// Horton is a Density Functional Theory program.
// Copyright (C) 2011-2012 Toon Verstraelen <Toon.Verstraelen@UGent.be>
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


#ifndef HORTON_GBASIS_FNS_H
#define HORTON_GBASIS_FNS_H

#include "calc.h"
#include "iter_pow.h"


class GB1GridFn : public GBCalculator  {
    protected:
        long shell_type0;
        const long dim_work, dim_output;
        const double *r0;    // The center of the basis function
        const double *point; // The grid point at which the fn is evaluated
        IterPow1 i1p;
    public:
        GB1GridFn(long max_shell_type, long dim_work, long dim_output);

        void reset(long shell_type0, const double* r0, const double* point);
        void cart_to_pure();
        const long get_shell_type0() const {return shell_type0;};

        long get_dim_work() {return dim_work;};
        long get_dim_output() {return dim_output;};
        virtual void add(double coeff, double alpha0, const double* scales0) = 0;
        virtual void compute_point_from_dm(double* work_basis, double* dm, long nbasis, double* output) = 0;
        virtual void compute_fock_from_pot(double* pot, double* work_basis, long nbasis, double* output) = 0;
    };


class GB1GridDensityFn : public GB1GridFn  {
    public:
        GB1GridDensityFn(long max_shell_type): GB1GridFn(max_shell_type, 1, 1) {};

        virtual void add(double coeff, double alpha0, const double* scales0);
        virtual void compute_point_from_dm(double* work_basis, double* dm, long nbasis, double* output);
        virtual void compute_fock_from_pot(double* pot, double* work_basis, long nbasis, double* output);
    };


class GB1GridGradientFn : public GB1GridFn  {
    public:
        GB1GridGradientFn(long max_shell_type): GB1GridFn(max_shell_type, 4, 3) {};

        virtual void add(double coeff, double alpha0, const double* scales0);
        virtual void compute_point_from_dm(double* work_basis, double* dm, long nbasis, double* output);
        virtual void compute_fock_from_pot(double* pot, double* work_basis, long nbasis, double* output);
    };


class GB2GridFn : public GBCalculator  {
    protected:
        long shell_type0, shell_type1;
        const double *r0, *r1;  // The centers of the basis functions
        const double *point;    // The grid point at which the fn is evaluated
        IterPow2 i2p;
    public:
        GB2GridFn(long max_shell_type);

        void reset(long shell_type0, long shell_type1, const double* r0, const double* r1, const double* point);
        void cart_to_pure();
        const long get_shell_type0() const {return shell_type0;};
        const long get_shell_type1() const {return shell_type1;};

        virtual void add(double coeff, double alpha0, double alpha1, const double* scales0, const double* scales1) = 0;
    };


class GB2HartreeGridFn : public GB2GridFn  {
    private:
        double* work_g0;
        double* work_g1;
        double* work_g2;
        double* work_boys;
    public:
        GB2HartreeGridFn(long max_shell_type);
        ~GB2HartreeGridFn();

        virtual void add(double coeff, double alpha0, double alpha1, const double* scales0, const double* scales1);
    };




#endif
