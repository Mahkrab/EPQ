// Free-slip slab shear should decay at the same physical rate at every depth.
// A Fourier reduction is exact for this periodic horizontal discrete operator;
// it exposes boundary truncation without pressure, gravity or PBF interference.
#include "qualification_viscosity.hpp"
#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
int main(int argc,char **argv) try {
    if(argc!=4)throw std::runtime_error("horizontal_n layers steps");
    const int n=std::stoi(argv[1]),layers=std::stoi(argv[2]),steps=std::stoi(argv[3]);
    if(n<12 || n>96 || layers<1 || layers>128 || steps<100)throw std::runtime_error("invalid slab request");
    constexpr double pi=3.14159265358979323846;const double length=.6,dx=length/n,h=4*dx,nu=.001,volume=dx*dx*dx;
    const double duration=1/(nu*std::pow(2*pi/length,2)),dt=duration/steps;
    std::vector<double> coupling(9),diagonal(9);
    for(int x=-4;x<=4;++x)for(int y=-4;y<=4;++y)for(int z=-4;z<=4;++z) {
        const auto pair=qualification::viscous_pair({x*dx,y*dx,z*dx},{1,0,0},h,nu,volume);
        coupling[y+4]+=pair.acceleration[0]*std::cos(2*pi*z/n);diagonal[y+4]+=pair.acceleration[0];
    }
    std::vector<double> a(layers,1),next(layers);std::cout<<std::setprecision(17)<<"{\"n\":"<<n<<",\"layers\":"<<layers<<",\"H\":"<<layers*dx<<",\"dt\":"<<dt<<",\"samples\":[";
    for(int step=0;step<=steps;++step) {
        if(step%(steps/20)==0 || step==steps) {
            if(step) {std::cout<<",";}
            std::cout<<"{\"time\":"<<step*dt<<",\"amplitudes\":[";
            for(int y=0;y<layers;++y) {if(y)std::cout<<",";std::cout<<a[y];}std::cout<<"]}";
        }
        if(step==steps)break;
        for(int y=0;y<layers;++y) {double rate=0;for(int offset=-4;offset<=4;++offset)if(y+offset>=0 && y+offset<layers)rate+=coupling[offset+4]*a[y+offset]-diagonal[offset+4]*a[y];next[y]=a[y]+dt*rate;}
        a.swap(next);
    }
    double mean=0;for(double value:a)mean+=value/layers;
    std::cout<<"],\"analytic_final_amplitude\":"<<std::exp(-1.)<<",\"mean_final_amplitude\":"<<mean<<",\"relative_error\":"<<mean/std::exp(-1.)-1<<",\"vertical_amplitude_spread\":"<<*std::max_element(a.begin(),a.end())-*std::min_element(a.begin(),a.end())<<"}\n";
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
