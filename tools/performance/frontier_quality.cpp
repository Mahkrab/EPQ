// Independent current-position density, support-cube volume and energy audits.
// Spatial search and all physical sums use binary64, outside solver timing.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>
using Point=std::array<float,3>;
using Cell=std::array<long long,3>;
static double quantile(std::vector<double> a,double q){if(a.empty())return 0;std::sort(a.begin(),a.end());return a[std::size_t(q*(a.size()-1))];}
static void read(const char *name,std::vector<Point>&p,std::vector<Point>&v){std::ifstream in(name,std::ios::binary);in.read(reinterpret_cast<char*>(p.data()),p.size()*sizeof(Point));in.read(reinterpret_cast<char*>(v.data()),v.size()*sizeof(Point));if(!in||in.peek()!=EOF)throw std::runtime_error("state length differs");for(auto *a:{&p,&v})for(auto x:*a)for(auto y:x)if(!std::isfinite(y))throw std::runtime_error("nonfinite state");}
int main(int argc,char **argv)try{
    if(argc!=11)throw std::runtime_error("state N h rest mass gy spacing upper initial pitch");
    const std::size_t n=std::stoull(argv[2]);const double h=std::stod(argv[3]),rest=std::stod(argv[4]),mass=std::stod(argv[5]),gy=std::stod(argv[6]),dx=std::stod(argv[7]),pitch=std::stod(argv[10]);
    if(!n||n>512000||h<=0||rest<=0||mass<=0||dx<=0||pitch<=0)throw std::runtime_error("invalid audit dimensions");
    std::array<double,3> upper{};if(std::sscanf(argv[8],"%lf,%lf,%lf",&upper[0],&upper[1],&upper[2])!=3)throw std::runtime_error("box required");
    std::vector<Point> p(n),v(n),p0(n),v0(n);read(argv[1],p,v);read(argv[9],p0,v0);
    std::map<Cell,std::vector<std::size_t>> grid;
    auto cell=[&](Point a){return Cell{(long long)std::floor(a[0]/h),(long long)std::floor(a[1]/h),(long long)std::floor(a[2]/h)};};
    for(std::size_t i=0;i<n;i++)grid[cell(p[i])].push_back(i);
    std::map<std::array<long long,2>,std::vector<std::array<double,2>>> columns;
    std::vector<double> compression,ratio,nearest,wall,bulk,surface;std::array<double,3> com{},momentum{};
    double K=0,P=0,K0=0,P0=0,violation=0,speed=0,mode=0,mode0=0,errorv=0;std::size_t coincidence=0,under=0;
    const double coeff=315/(64*std::acos(-1.)*std::pow(h,9));
    for(std::size_t i=0;i<n;i++){
        double density=coeff*std::pow(h*h,3),close=h;bool above=false;auto origin=cell(p[i]);
        for(int a=-1;a<=1;a++)for(int b=-1;b<=1;b++)for(int c=-1;c<=1;c++){
            auto found=grid.find({origin[0]+a,origin[1]+b,origin[2]+c});if(found==grid.end())continue;
            for(auto j:found->second)if(j!=i){double d2=0;for(int k=0;k<3;k++){double d=double(p[i][k])-p[j][k];d2+=d*d;}close=std::min(close,std::sqrt(d2));if(d2<h*h)density+=coeff*std::pow(h*h-d2,3);double dy=double(p[j][1])-p[i][1];if(dy>.5*dx&&d2-dy*dy<dx*dx&&dy<1.5*dx)above=true;}
        }
        const double r=density/rest,e=std::max(0.,r-1);ratio.push_back(r);compression.push_back(e);nearest.push_back(close);if(close==0)coincidence++;if(r<.9)under++;
        double wd=upper[0],s2=0,initial2=0,ev=0;
        for(int k=0;k<3;k++){wd=std::min(wd,std::min(double(p[i][k]),upper[k]-p[i][k]));violation=std::max(violation,std::max(-double(p[i][k]),double(p[i][k])-upper[k]));com[k]+=p[i][k]/double(n);momentum[k]+=v[i][k]/double(n);s2+=double(v[i][k])*v[i][k];initial2+=double(v0[i][k])*v0[i][k];double d=double(v[i][k])-v0[i][k];ev+=d*d;}
        (wd<h?wall:bulk).push_back(e);if(!above)surface.push_back(r);
        K+=.5*s2/n;P-=gy*p[i][1]/n;K0+=.5*initial2/n;P0-=gy*p0[i][1]/n;speed=std::max(speed,std::sqrt(s2));errorv+=ev/n;
        mode+=double(v[i][0])*v0[i][0];mode0+=double(v0[i][0])*v0[i][0];
        const double lo=std::max(0.,double(p[i][1])-dx/2),hi=std::min(upper[1],double(p[i][1])+dx/2);
        if(hi>lo){long long ix0=std::ceil((p[i][0]-dx/2)/pitch-.5),ix1=std::floor((p[i][0]+dx/2)/pitch-.5),iz0=std::ceil((p[i][2]-dx/2)/pitch-.5),iz1=std::floor((p[i][2]+dx/2)/pitch-.5);
            for(auto ix=ix0;ix<=ix1;ix++)for(auto iz=iz0;iz<=iz1;iz++){double x=(ix+.5)*pitch,z=(iz+.5)*pitch;if(x>=0&&x<upper[0]&&z>=0&&z<upper[2])columns[{ix,iz}].push_back({lo,hi});}}
    }
    double occupied=0,maxheight=0;for(auto &[key,intervals]:columns){std::sort(intervals.begin(),intervals.end());double lo=intervals[0][0],hi=intervals[0][1],sum=0;for(auto a:intervals){if(a[0]>hi){sum+=hi-lo;lo=a[0];hi=a[1];}else hi=std::max(hi,a[1]);}sum+=hi-lo;occupied+=sum*pitch*pitch;maxheight=std::max(maxheight,hi);}
    double meanrho=0;for(auto r:ratio)meanrho+=r/n;
    std::cout.precision(17);std::cout<<"{\"particles\":"<<n<<",\"p95_compression\":"<<quantile(compression,.95)<<",\"max_compression\":"<<quantile(compression,1)<<",\"mean_density_ratio\":"<<meanrho<<",\"under_density_fraction\":"<<double(under)/n<<",\"min_separation\":"<<quantile(nearest,0)<<",\"coincidences\":"<<coincidence<<",\"boundary_violation\":"<<violation<<",\"max_speed\":"<<speed<<",\"com\":["<<com[0]<<","<<com[1]<<","<<com[2]<<"],\"mean_velocity\":["<<momentum[0]<<","<<momentum[1]<<","<<momentum[2]<<"],\"kinetic_J_kg\":"<<K<<",\"potential_J_kg\":"<<P<<",\"mechanical_excess_relative\":"<<(K+P-K0-P0)/std::max(K0+P0,1e-30)<<",\"shear_projection\":"<<(mode0?mode/mode0:0)<<",\"velocity_error_relative\":"<<std::sqrt(errorv/std::max(2*K0,1e-30))<<",\"occupied_support_volume\":"<<occupied<<",\"physical_volume\":"<<n*mass/1000<<",\"height_max\":"<<maxheight<<",\"volume_pitch\":"<<pitch<<",\"near_wall_p95\":"<<quantile(wall,.95)<<",\"bulk_p95\":"<<quantile(bulk,.95)<<",\"top_exposed_density_p05\":"<<quantile(surface,.05)<<"}\n";
    return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<"\n";return 1;}
