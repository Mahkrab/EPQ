// Affine, rigid and perturbed-cloud tests check the weak operator independently
// of shear eigenmode agreement. Every force field remains available for audit.
#include "traction_viscosity.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cstdint>
#include <omp.h>
int main(int argc,char **argv) try {
    if(argc!=5)throw std::runtime_error("jitter profile output threads");
    const double jitter=std::stod(argv[1]);const std::string profile=argv[2];omp_set_dynamic(0);omp_set_num_threads(std::stoi(argv[4]));
    std::vector<traction::V> p,v,direction;constexpr double dx=.02,nu=.001;
    for(int x=0;x<6;++x)for(int y=0;y<6;++y)for(int z=0;z<6;++z) {
        traction::V r{dx*(x-2.5),dx*(y-2.5),dx*(z-2.5)};
        for(int k=0;k<3;++k)r[k]+=jitter*dx*std::sin((x*37+y*17+z*11+k*7)*1.234);
        p.push_back(traction::plus(r,{.5,.5,.5}));traction::V u{};
        if(profile=="translation")u={.2,-.3,.1};
        else if(profile=="rotation")u={-.4*r[2]-.2*r[1],.2*r[0]-.3*r[2],.3*r[1]+.4*r[0]};
        else if(profile=="affine")u={.3*r[0]+.4*r[1],.4*r[0]-.2*r[1]+.1*r[2],.1*r[1]-.1*r[2]};
        else if(profile=="nonlinear")u={std::sin(7*r[1]),std::cos(5*r[2]),std::sin(3*r[0])};
        else if(profile=="checkerboard")u={(y%2) ? -1. : 1.,0,0};
        else throw std::runtime_error("unknown invariant profile");
        v.push_back(u);direction.push_back({std::sin(13*r[0]+3*r[2]),std::cos(7*r[1]),std::sin(11*r[2]-r[0])});
    }
    traction::Operator op(p,{1,1,1},{false,false,false},{0,0,0,0,0,0},2*dx);std::vector<traction::V> a;
    const double power=op.apply(v,nu,a);double work=0,maximum=0;traction::V linear{},angular{};
    for(unsigned i=0;i<p.size();++i) {work+=traction::dot(v[i],a[i])/p.size();linear=traction::plus(linear,traction::times(a[i],1./p.size()));angular=traction::plus(angular,traction::times({p[i][1]*a[i][2]-p[i][2]*a[i][1],p[i][2]*a[i][0]-p[i][0]*a[i][2],p[i][0]*a[i][1]-p[i][1]*a[i][0]},1./p.size()));maximum=std::max(maximum,std::sqrt(traction::dot(a[i],a[i])));}
    const double epsilon=1e-6;auto positive=v,negative=v;for(unsigned i=0;i<v.size();++i) {positive[i]=traction::plus(v[i],traction::times(direction[i],epsilon));negative[i]=traction::minus(v[i],traction::times(direction[i],epsilon));}
    std::vector<traction::V> scratch;const double finite_difference=(op.apply(positive,nu,scratch)-op.apply(negative,nu,scratch))/(4*epsilon);double derivative=0;for(unsigned i=0;i<v.size();++i)derivative-=traction::dot(a[i],direction[i])/v.size();
    std::ofstream out(argv[3],std::ios::binary);std::uint32_t n=p.size();out.write(reinterpret_cast<const char*>(&n),4);for(auto values:{&p,&v,&a})out.write(reinterpret_cast<const char*>(values->data()),values->size()*sizeof(traction::V));if(!out)throw std::runtime_error("invariant output failed");
    std::cout<<std::setprecision(17)<<"{\"profile\":\""<<profile<<"\",\"jitter\":"<<jitter<<",\"power\":"<<power<<",\"work\":"<<work<<",\"maximum_acceleration\":"<<maximum<<",\"linear\":["<<linear[0]<<","<<linear[1]<<","<<linear[2]<<"],\"angular\":["<<angular[0]<<","<<angular[1]<<","<<angular[2]<<"],\"finite_difference\":"<<finite_difference<<",\"adjoint_derivative\":"<<derivative<<",\"condition\":"<<op.maximum_condition<<",\"linear_error\":"<<op.maximum_linear_error<<"}\n";
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
