// Independent all-pairs binary64 observations: no solver kernel, neighbour grid,
// multipliers or classifications derived from measured density are reused.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>
using Point=std::array<double,3>;
template<class T>static void read(std::istream &f,T *p,std::size_t n) {
    f.read(reinterpret_cast<char *>(p),n*sizeof(T));if(!f)throw std::runtime_error("truncated raw observation");
}
static double quantile(std::vector<double> v,double q) {
    if(v.empty())return -1;
    std::sort(v.begin(),v.end());return v[static_cast<std::size_t>(q*(v.size()-1))];
}
int main(int argc,char **argv)try {
    if(argc!=3)throw std::runtime_error("raw observations boundary-enabled");
    const bool boundary=std::stoi(argv[2]);std::ifstream f(argv[1],std::ios::binary);
    std::uint32_t head[4];double c[7];read(f,head,4);read(f,c,7);
    if(head[0]!=0x50424632 || !head[1] || head[1]>100000 || head[2]>1000000)throw std::runtime_error("invalid header");
    const unsigned n=head[1];std::vector<Point> wall(head[2]),p(n),v(n);read(f,wall.data(),wall.size());
    const double dt=c[0],h=c[1],h2=h*h,rest=c[2],mass=c[3],H=n*mass/(1000*c[4]*c[6]);
    const double coeff=315/(64*std::acos(-1.)*std::pow(h,9));
    auto W=[&](Point a,Point b) {double r2=0;for(unsigned k=0;k<3;++k)r2+=(a[k]-b[k])*(a[k]-b[k]);
        const double t=std::max(0.,h2-r2);return coeff*t*t*t;};
    std::cout<<std::setprecision(17);
    while(f.peek()!=EOF) {
        std::uint32_t step;read(f,&step,1);read(f,p.data(),n);read(f,v.data(),n);
        std::vector<double> positive,bulk,surface,wall_error,fluid_error,height;
        double nearest=h,violation=0,kinetic=0,potential=0;Point centre{},momentum{};
        for(unsigned i=0;i<n;++i) {
            for(unsigned k=0;k<3;++k) {
                if(!std::isfinite(p[i][k]) || !std::isfinite(v[i][k]))throw std::runtime_error("nonfinite state");
                centre[k]+=p[i][k]/n;momentum[k]+=v[i][k]/n;
                violation=std::max(violation,std::max(-p[i][k],p[i][k]-c[4+k]));
                kinetic+=v[i][k]*v[i][k]/(2*n);
            }
            potential+=9.81*p[i][1]/n;height.push_back(p[i][1]);double density=0;
            for(unsigned j=0;j<n;++j) {
                density+=W(p[i],p[j]);
                if(j!=i) {double r2=0;for(unsigned k=0;k<3;++k)r2+=(p[i][k]-p[j][k])*(p[i][k]-p[j][k]);nearest=std::min(nearest,std::sqrt(r2));}
            }
            fluid_error.push_back(density/rest-1);
            if(boundary)for(const auto &b:wall)density+=W(p[i],b);
            double error=density/rest-1;positive.push_back(std::max(0.,error));
            double distance=std::min({p[i][0],p[i][1],p[i][2],c[4]-p[i][0],c[5]-p[i][1],c[6]-p[i][2]});
            if(distance<h)wall_error.push_back(error);
            if(p[i][1]>H-h)surface.push_back(error);
            if(distance>=h && p[i][1]<=H-h)bulk.push_back(std::abs(error));
        }
        std::cout<<"{\"step\":"<<step<<",\"time_s\":"<<step*dt<<",\"p95_compression\":"<<quantile(positive,.95)
          <<",\"max_compression\":"<<quantile(positive,1)<<",\"minimum_separation_m\":"<<nearest
          <<",\"boundary_violation_m\":"<<violation<<",\"kinetic_J_kg\":"<<kinetic<<",\"mechanical_J_kg\":"<<kinetic+potential
          <<",\"centre\":["<<centre[0]<<","<<centre[1]<<","<<centre[2]<<"],\"mean_velocity\":["<<momentum[0]<<","<<momentum[1]<<","<<momentum[2]
          <<"],\"expected_depth_m\":"<<H<<",\"surface_height_m\":"<<quantile(height,.95)+.025
          <<",\"centroid_relative_error\":"<<std::abs(centre[1]-H/2)/(H/2)
          <<",\"surface_relative_error\":"<<std::abs(quantile(height,.95)+.025-H)/H
          <<",\"bulk_count\":"<<bulk.size()<<",\"bulk_p95_absolute_error\":"<<quantile(bulk,.95)
          <<",\"surface_count\":"<<surface.size()<<",\"surface_signed_error_p05\":"<<quantile(surface,.05)
          <<",\"surface_signed_error_p95\":"<<quantile(surface,.95)
          <<",\"wall_signed_error_p05\":"<<quantile(wall_error,.05)<<",\"wall_signed_error_p95\":"<<quantile(wall_error,.95)
          <<",\"fluid_only_signed_error_p05\":"<<quantile(fluid_error,.05)<<",\"fluid_only_signed_error_p95\":"<<quantile(fluid_error,.95)<<"}\n";
    }
}catch(const std::exception &e){std::cerr<<e.what()<<"\n";return 1;}
