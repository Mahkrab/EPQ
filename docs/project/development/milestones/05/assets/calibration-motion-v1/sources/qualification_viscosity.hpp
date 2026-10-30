// A symmetric central strain operator models Newtonian viscosity in 3D.
// Equal physical particle volumes give equal-and-opposite central impulses.
#pragma once
#include <array>
#include <cmath>
namespace qualification {
using Vector=std::array<double,3>;
struct PairRate {Vector acceleration{};double row=0;};
inline PairRate viscous_pair(Vector r,Vector difference,double h,double nu,double volume) {
    double r2=0,projection=0;
    for(unsigned k=0;k<3;++k) {r2+=r[k]*r[k];projection+=r[k]*difference[k];}
    if(r2==0 || r2>=h*h)return {};
    const double t=1-std::sqrt(r2)/h;
    constexpr double pi=3.14159265358979323846;
    const double row=10*nu*volume*420/(2*pi*h*h*h*h*h)*t*t*t;
    PairRate result;result.row=row;
    for(unsigned k=0;k<3;++k)result.acceleration[k]=row*r[k]*projection/r2;
    return result;
}
}
