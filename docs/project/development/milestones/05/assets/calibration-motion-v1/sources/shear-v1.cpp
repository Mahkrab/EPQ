// A fixed periodic lattice isolates the dimensional viscosity operator from PBF.
// The transverse Fourier mode has the independent decay exp(-nu*k*k*t).
#include "qualification_viscosity.hpp"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
int main(int argc,char **argv) try {
    if(argc!=4)throw std::runtime_error("n nu time_steps");
    const int n=std::stoi(argv[1]),steps=std::stoi(argv[3]);const double nu=std::stod(argv[2]);
    if(n<6 || n>128 || nu<=0 || steps<100)throw std::runtime_error("invalid shear request");
    constexpr double pi=3.14159265358979323846;const double length=.6,dx=length/n,h=2*dx,volume=dx*dx*dx;
    const double rate=nu*std::pow(2*pi/length,2),duration=1/rate,dt=duration/steps;
    std::vector<double> v(n),next(n);for(int y=0;y<n;++y)v[y]=std::sin(2*pi*(y+.5)/n);
    double row=0,rigid_error=0;std::vector<double> stencil(5);
    for(int x=-2;x<=2;++x)for(int y=-2;y<=2;++y)for(int z=-2;z<=2;++z) {
        qualification::Vector r{dx*x,dx*y,dx*z};
        const auto unit=qualification::viscous_pair(r,{1,0,0},h,nu,volume);
        stencil[y+2]+=unit.acceleration[0];row+=unit.row;
        const auto rotation=qualification::viscous_pair(r,{-r[1],r[0],0},h,nu,volume);
        for(double a:rotation.acceleration)rigid_error=std::max(rigid_error,std::abs(a));
    }
    if(row*dt>1)throw std::runtime_error("explicit shear row bound exceeded");
    double previous_energy=.25,max_energy_gain=0;
    for(int step=1;step<=steps;++step) {
        for(int y=0;y<n;++y) {double a=0;for(int offset=-2;offset<=2;++offset)a+=stencil[offset+2]*(v[(y+offset+n)%n]-v[y]);next[y]=v[y]+dt*a;}
        v.swap(next);double energy=0;for(double u:v)energy+=u*u/(2*n);
        max_energy_gain=std::max(max_energy_gain,energy-previous_energy);previous_energy=energy;
    }
    double amplitude=0,mean=0;for(int y=0;y<n;++y) {amplitude+=2*v[y]*std::sin(2*pi*(y+.5)/n)/n;mean+=v[y]/n;}
    std::cout<<std::setprecision(17)<<"{\"n\":"<<n<<",\"nu\":"<<nu<<",\"steps\":"<<steps<<",\"duration\":"<<duration<<",\"observed_amplitude\":"<<amplitude<<",\"analytic_amplitude\":"<<std::exp(-1.)<<",\"relative_error\":"<<amplitude/std::exp(-1.)-1<<",\"mean_velocity\":"<<mean<<",\"maximum_energy_increase\":"<<max_energy_gain<<",\"rigid_rotation_error\":"<<rigid_error<<",\"max_row_dt\":"<<row*dt<<"}\n";
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
