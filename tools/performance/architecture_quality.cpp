// Independent binary64 health measurements use current-position neighbours,
// rather than the solver's frozen prediction-time rows or its density buffers.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

using Point=std::array<float,3>;
using Cell=std::array<long long,3>;
static double quantile(std::vector<double> v,double q) {
    std::sort(v.begin(),v.end());return v[static_cast<std::size_t>(q*(v.size()-1))];
}
int main(int argc,char **argv) try {
    if (argc!=7) throw std::runtime_error("snapshot count radius normalised-rest-density box-upper reference-or-none");
    const std::size_t n=std::stoull(argv[2]);const double h=std::stod(argv[3]),rest=std::stod(argv[4]);
    if (!n || n>512000 || !(h>0) || !(rest>0)) throw std::runtime_error("invalid health request");
    std::vector<Point> p(n),v(n);
    auto read=[&](const char *path,std::vector<Point> &a,std::vector<Point> &b) {
        std::ifstream file(path,std::ios::binary);
        file.read(reinterpret_cast<char *>(a.data()),n*sizeof(Point));
        file.read(reinterpret_cast<char *>(b.data()),n*sizeof(Point));
        if (!file || file.peek()!=EOF) throw std::runtime_error("snapshot length differs");
        for (const auto *points:{&a,&b}) for (const auto &point:*points) for (float x:point)
            if (!std::isfinite(x)) throw std::runtime_error("nonfinite snapshot");
    };
    read(argv[1],p,v);
    std::array<double,3> upper{};
    if (std::sscanf(argv[5],"%lf,%lf,%lf",&upper[0],&upper[1],&upper[2])!=3)
        throw std::runtime_error("box upper coordinates required");
    std::map<Cell,std::vector<std::size_t>> grid;
    auto cell=[&](Point a) {return Cell{static_cast<long long>(std::floor(a[0]/h)),
        static_cast<long long>(std::floor(a[1]/h)),static_cast<long long>(std::floor(a[2]/h))};};
    for (std::size_t i=0;i<n;++i) grid[cell(p[i])].push_back(i);
    const double coefficient=315/(64*std::acos(-1.0)*std::pow(h,9));
    std::vector<double> neighbours,density,compression,absolute,spacing,wall_compression,bulk_compression;
    double density_sum=0,compression_sum=0,kinetic=0,potential=0,max_speed=0,violation=0;
    std::array<double,3> centre{};
    std::size_t duplicates=0;
    for (std::size_t i=0;i<n;++i) {
        const auto origin=cell(p[i]);double rho=coefficient*std::pow(h*h,3),nearest=h;unsigned count=0;
        for (int x=-1;x<=1;++x) for (int y=-1;y<=1;++y) for (int z=-1;z<=1;++z) {
            const auto found=grid.find({origin[0]+x,origin[1]+y,origin[2]+z});
            if (found==grid.end()) continue;
            for (const auto j:found->second) if (j!=i) {
                double d2=0;for (unsigned k=0;k<3;++k) {double d=static_cast<double>(p[i][k])-p[j][k];d2+=d*d;}
                nearest=std::min(nearest,std::sqrt(d2));
                if (d2<h*h) {++count;rho+=coefficient*std::pow(h*h-d2,3);}
            }
        }
        if (nearest==0) ++duplicates;
        const double ratio=rho/rest,positive=std::max(0.0,ratio-1);
        neighbours.push_back(count);density.push_back(ratio);compression.push_back(positive);
        absolute.push_back(std::abs(ratio-1));spacing.push_back(nearest);
        density_sum+=ratio;compression_sum+=positive;
        double wall_distance=upper[0];
        for (unsigned k=0;k<3;++k)
            wall_distance=std::min(wall_distance,std::min(static_cast<double>(p[i][k]),upper[k]-p[i][k]));
        (wall_distance<h ? wall_compression : bulk_compression).push_back(positive);
        double speed2=0;for (unsigned k=0;k<3;++k) {
            speed2+=static_cast<double>(v[i][k])*v[i][k];centre[k]+=p[i][k]/static_cast<double>(n);
            violation=std::max(violation,std::max(-static_cast<double>(p[i][k]),p[i][k]-upper[k]));
        }
        kinetic+=0.5*speed2/n;potential+=9.81*p[i][1]/n;max_speed=std::max(max_speed,std::sqrt(speed2));
    }
    double p_rms=0,p_max=0,v_rms=0,v_max=0;std::size_t exact=0;
    const bool reference=std::string(argv[6])!="none";
    if (reference) {
        std::vector<Point> rp(n),rv(n);read(argv[6],rp,rv);
        for (std::size_t i=0;i<n;++i) {
            double dp=0,dv=0;for (unsigned k=0;k<3;++k) {
                const double a=static_cast<double>(p[i][k])-rp[i][k],b=static_cast<double>(v[i][k])-rv[i][k];
                dp+=a*a;dv+=b*b;if (p[i][k]==rp[i][k]) ++exact;
            }
            p_rms+=dp/n;v_rms+=dv/n;p_max=std::max(p_max,std::sqrt(dp));v_max=std::max(v_max,std::sqrt(dv));
        }
    }
    std::cout.precision(17);
    std::cout<<"{\"particles\":"<<n<<",\"current_neighbours\":{\"min\":"<<quantile(neighbours,0)
        <<",\"median\":"<<quantile(neighbours,.5)<<",\"p95\":"<<quantile(neighbours,.95)<<",\"max\":"<<quantile(neighbours,1)
        <<"},\"density_ratio\":{\"mean\":"<<density_sum/n<<",\"p05\":"<<quantile(density,.05)
        <<",\"median\":"<<quantile(density,.5)<<",\"p95\":"<<quantile(density,.95)<<",\"max\":"<<quantile(density,1)
        <<"},\"positive_density_error\":{\"mean\":"<<compression_sum/n<<",\"p95\":"<<quantile(compression,.95)
        <<",\"max\":"<<quantile(compression,1)<<"},\"absolute_density_error_p95\":"<<quantile(absolute,.95)
        <<",\"nearest_separation_m\":{\"min\":"<<quantile(spacing,0)<<",\"median\":"<<quantile(spacing,.5)
        <<"},\"coincident_rows\":"<<duplicates<<",\"maximum_speed_m_s\":"<<max_speed<<",\"boundary_violation_m\":"<<violation
        <<",\"centre_m\":["<<centre[0]<<","<<centre[1]<<","<<centre[2]<<"],\"kinetic_j_kg\":"<<kinetic
        <<",\"potential_j_kg\":"<<potential<<",\"reference\":"<<(reference?"true":"false")
        <<",\"position_rms_m\":"<<std::sqrt(p_rms)<<",\"position_max_m\":"<<p_max
        <<",\"velocity_rms_m_s\":"<<std::sqrt(v_rms)<<",\"velocity_max_m_s\":"<<v_max
        <<",\"equal_position_components\":"<<exact
        <<",\"near_wall\":{\"count\":"<<wall_compression.size()<<",\"positive_density_error_p95\":";
    if (wall_compression.empty()) std::cout<<"null";else std::cout<<quantile(wall_compression,.95);
    std::cout<<"},\"away_from_walls\":{\"count\":"<<bulk_compression.size()<<",\"positive_density_error_p95\":";
    if (bulk_compression.empty()) std::cout<<"null";else std::cout<<quantile(bulk_compression,.95);
    std::cout<<"}}\n";
    return 0;
} catch (const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
