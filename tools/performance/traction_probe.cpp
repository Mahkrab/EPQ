// One native action checks the implementation against independently assembled
// Fourier matrices; prescribed positions isolate viscosity from pressure.
#include "traction_viscosity.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <cstdint>
#include <omp.h>
int main(int argc,char **argv) try {
    if(argc!=7)throw std::runtime_error("layers mode L support output threads");
    const int layers=std::stoi(argv[1]);const std::string mode=argv[2];const double length=std::stod(argv[3]),support=std::stod(argv[4]);
    const double H=.05,dx=H/layers;const int nx=std::lround(length/dx);if(layers<2 || layers>24 || nx<4 || nx>128 || std::abs(nx*dx-length)>1e-10)throw std::runtime_error("invalid probe lattice");
    omp_set_dynamic(0);omp_set_num_threads(std::stoi(argv[6]));
    std::array<int,6> boundary{};double ky=0,kz=0;
    if(mode=="horizontal-natural")kz=2*3.14159265358979323846/length;
    else if(mode=="horizontal-slip") {kz=2*3.14159265358979323846/length;boundary[2]=boundary[3]=1;}
    else if(mode=="vertical-noslip") {ky=3.14159265358979323846/H;boundary[2]=boundary[3]=2;}
    else if(mode=="vertical-slip") {ky=3.14159265358979323846/H;boundary[2]=boundary[3]=1;}
    else if(mode=="vertical-mixed") {ky=3.14159265358979323846/(2*H);boundary[2]=2;}
    else throw std::runtime_error("unknown probe mode");
    std::vector<traction::V> p,v;
    for(int x=0;x<nx;++x)for(int y=0;y<layers;++y)for(int z=0;z<nx;++z) {traction::V point{dx*(x+.5),dx*(y+.5),dx*(z+.5)};p.push_back(point);double u=ky ? (mode=="vertical-slip" ? std::cos(ky*point[1]) : std::sin(ky*point[1])) : std::sin(kz*point[2]);v.push_back({u,0,0});}
    traction::Operator op(p,{length,H,length},{true,false,true},boundary,support*dx);std::vector<traction::V> a;
    const double power=op.apply(v,.001,a);double work=0;for(unsigned i=0;i<v.size();++i)work+=traction::dot(v[i],a[i])/v.size();
    std::ofstream out(argv[5],std::ios::binary);std::uint32_t count=p.size();out.write(reinterpret_cast<const char*>(&count),4);out.write(reinterpret_cast<const char*>(p.data()),p.size()*sizeof(traction::V));out.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(traction::V));out.write(reinterpret_cast<const char*>(a.data()),a.size()*sizeof(traction::V));if(!out)throw std::runtime_error("probe write failed");
    std::cout<<std::setprecision(17)<<"{\"particles\":"<<p.size()<<",\"layers\":"<<layers<<",\"mode\":\""<<mode<<"\",\"L\":"<<length<<",\"dx\":"<<dx<<",\"power\":"<<power<<",\"v_dot_a\":"<<work<<",\"max_condition\":"<<op.maximum_condition<<",\"linear_error\":"<<op.maximum_linear_error<<",\"eigenvalue_bound\":"<<op.eigenvalue_bound(.001)<<",\"edges\":"<<op.edge_count()<<"}\n";
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
