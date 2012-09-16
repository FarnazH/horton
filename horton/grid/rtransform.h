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

#ifndef HORTON_GRID_RTRANSFORM_H
#define HORTON_GRID_RTRANSFORM_H

class BaseRTransform {
    private:
        int npoint;

    public:
        BaseRTransform(int npoint);
        virtual ~BaseRTransform() {};
        virtual double radius(double t) = 0;
        virtual double deriv(double t) = 0;
        virtual double inv(double r) = 0;

        void radius_array(double* t, double* r, int n);
        void deriv_array(double* t, double* d, int n);
        void inv_array(double* r, double* t, int n);
        int get_npoint() {return npoint;};
    };


class IdentityRTransform : public BaseRTransform {
    public:
        IdentityRTransform(int npoint): BaseRTransform(npoint) {};
        virtual double radius(double t);
        virtual double deriv(double t);
        virtual double inv(double r);
    };


class LinearRTransform : public BaseRTransform {
    private:
        double rmin, rmax, alpha;
    public:
        LinearRTransform(double rmin, double rmax, int npoint);
        virtual double radius(double t);
        virtual double deriv(double t);
        virtual double inv(double r);

        double get_rmin() {return rmin;};
        double get_rmax() {return rmax;};
        double get_alpha() {return alpha;};
    };


class LogRTransform : public BaseRTransform {
    private:
        double rmin, rmax, alpha;
    public:
        LogRTransform(double rmin, double rmax, int npoint);
        virtual double radius(double t);
        virtual double deriv(double t);
        virtual double inv(double r);

        double get_rmin() {return rmin;};
        double get_rmax() {return rmax;};
        double get_alpha() {return alpha;};
    };


#endif
