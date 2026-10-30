// Spatial refinement of the isolated C2 model holds the physical collision
// geometry and total mass fixed. Each resolution owns an explicit observation
// stream; solver timings exclude those observations and independent audits.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <chrono>
#include <iomanip>
#include <omp.h>
#include <atomic>

using V=std::array<double,3>;
using Cell=std::array<int,3>;
static V add(V a,V b) {for(unsigned k=0;k<3;++k)a[k]+=b[k];return a;}
static V sub(V a,V b) {for(unsigned k=0;k<3;++k)a[k]-=b[k];return a;}
static V mul(V a,double b) {for(double &v:a)v*=b;return a;}
static double dot(V a,V b) {double s=0;for(unsigned k=0;k<3;++k)s+=a[k]*b[k];return s;}
constexpr double pi=3.14159265358979323846;
static double dx=.05,h=.1,w_coefficient=0,g_coefficient=0;
static double weight(double r2) {
    if(r2>=h*h)return 0;
    double t=1-std::sqrt(r2)/h,t2=t*t;
    return w_coefficient*t2*t2*(5-4*t);
}
static V gradient(V d,bool) {
    double r2=dot(d,d);if(r2==0 || r2>=h*h)return {};
    double t=1-std::sqrt(r2)/h;return mul(d,g_coefficient*t*t*t);
}
struct Scene {std::vector<V> p,v,wall;V upper;};
static Scene scene(const std::string &name,int n,double layers) {
    Scene s;s.upper={1.2,1.2,.8};
    auto sample=[&](V lower,V extent,std::array<int,3> count,V velocity) {
        for(int x=0;x<count[0];++x)for(int y=0;y<count[1];++y)for(int z=0;z<count[2];++z) {
            V p{};const int index[]={x,y,z};
            for(unsigned k=0;k<3;++k)p[k]=lower[k]+extent[k]*(index[k]+.5)/count[k];
            s.p.push_back(p);s.v.push_back(velocity);
        }
    };
    if(name=="collision") {
        sample({.1,.375,.2},{.3,.3,.3},{n,n,n},{.5,0,0});
        sample({.8,.375,.2},{.3,.3,.3},{n,n,n},{-.5,0,0});
    } else if(name=="flat")sample({0,0,0},{1.2,.05625,.8},{4*n,n/6,3*n},{});
    else if(name=="depth") {
        const int ny=static_cast<int>(std::floor(layers));
        const double desired_nz=(8*n/3)*layers/ny;
        const int nz=static_cast<int>(std::lround(desired_nz));
        if(std::abs(nz-desired_nz)>1e-9)throw std::runtime_error("depth does not preserve equal particle volumes");
        sample({0,0,0},{1.2,layers*dx,.8},{4*n,ny,nz},{});
    }
    else if(name=="depth-ceil") {
        const int ny=static_cast<int>(std::ceil(layers));
        const double target=4*n*(8*n/3)*layers;
        const int count=static_cast<int>(std::lround(target));
        if(std::abs(count-target)>1e-9 || count%ny)throw std::runtime_error("depth cannot preserve equal particle volumes");
        const int horizontal=count/ny;int best_x=1,best_z=horizontal;double best=1e100;
        for(int nx=1;nx<=horizontal;++nx)if(horizontal%nx==0) {
            int nz=horizontal/nx;
            double x=std::log(1.2/nx/dx),z=std::log(.8/nz/dx),score=x*x+z*z;
            if(score<best) {best=score;best_x=nx;best_z=nz;}
        }
        sample({0,0,0},{1.2,layers*dx,.8},{best_x,ny,best_z},{});
    }
    else throw std::runtime_error("unknown spatial scene");
    const int cells[]={4*n,4*n,8*n/3};
    for(int x=-2;x<cells[0]+2;++x)for(int y=-2;y<cells[1]+2;++y)for(int z=-2;z<cells[2]+2;++z)
        if(x<0 || y<0 || z<0 || x>=cells[0] || y>=cells[1] || z>=cells[2])
            s.wall.push_back({dx*(x+.5),dx*(y+.5),dx*(z+.5)});
    return s;
}
struct Search {
    std::array<int,3> dims;
    std::vector<std::vector<unsigned>> bins;
    const std::vector<V> *positions=nullptr;
    explicit Search(V upper) {
        for(unsigned k=0;k<3;++k)dims[k]=int(std::ceil(upper[k]/h))+6;
        bins.resize(static_cast<std::size_t>(dims[0])*dims[1]*dims[2]);
    }
    Cell cell(V p) const {return {int(std::floor(p[0]/h))+3,int(std::floor(p[1]/h))+3,int(std::floor(p[2]/h))+3};}
    std::size_t key(Cell c) const {return (static_cast<std::size_t>(c[0])*dims[1]+c[1])*dims[2]+c[2];}
    bool valid(Cell c) const {return c[0]>=0 && c[1]>=0 && c[2]>=0 && c[0]<dims[0] && c[1]<dims[1] && c[2]<dims[2];}
    void build(const std::vector<V> &p) {
        positions=&p;for(auto &b:bins)b.clear();
        for(unsigned i=0;i<p.size();++i) {auto c=cell(p[i]);if(!valid(c))throw std::runtime_error("search bounds exceeded");bins[key(c)].push_back(i);}
    }
    std::vector<unsigned> row(V p) const {
        std::vector<unsigned> result;auto c=cell(p);
        for(int x=-1;x<=1;++x)for(int y=-1;y<=1;++y)for(int z=-1;z<=1;++z) {
            Cell q{c[0]+x,c[1]+y,c[2]+z};if(!valid(q))continue;
            for(auto j:bins[key(q)]) {V d=sub(p,(*positions)[j]);if(dot(d,d)<h*h)result.push_back(j);}
        }
        std::sort(result.begin(),result.end());return result;
    }
};
static void write_bytes(const void *p,std::size_t n) {std::cout.write(static_cast<const char *>(p),n);if(!std::cout)throw std::runtime_error("observation write failed");}

int main(int argc,char **argv) try {
    if(argc!=10)throw std::runtime_error("scene n layers dt duration iterations boundary inset_fraction threads");
    const std::string name=argv[1];const int resolution=std::stoi(argv[2]);const double layers=std::stod(argv[3]);
    const double dt=std::stod(argv[4]),duration=std::stod(argv[5]);
    const unsigned iterations=std::stoul(argv[6]);const bool boundary=std::stoi(argv[7]);
    const double inset_fraction=std::stod(argv[8]);const int threads=std::stoi(argv[9]);
    if(!(resolution>=6 && resolution<=36 && resolution%6==0 && layers>=1 && layers<=24 && dt>0 && dt<=.02 && duration>=0 && duration<=12 && duration/dt<=100000 && iterations>0 && iterations<=128 && inset_fraction>=0 && inset_fraction<=.5 && threads>0 && threads<=24))
        throw std::runtime_error("invalid spatial request");
    dx=.3/resolution;h=2*dx;w_coefficient=21/(2*pi*h*h*h);g_coefficient=-20*w_coefficient/(h*h);
    const double base_mass=1000/8270.744069418484;
    const double mass=base_mass*216/std::pow(resolution,3),rest=1000/mass;
    const double eps=.02/(h*h),scale=.5,inset=inset_fraction*dx,contact_distance=.51*dx;
    const bool clamp=true,poly=true,refresh=true,contact=true;
    omp_set_dynamic(0);omp_set_num_threads(threads);
    Scene s=scene(name,resolution,layers);const unsigned n=s.p.size(),steps=std::lround(duration/dt),stride=std::max(1L,std::lround(.05/dt));
    const std::uint32_t header[]={0x50424634U,n,static_cast<unsigned>(s.wall.size()),steps};write_bytes(header,sizeof(header));
    const double constants[]={dt,h,rest,mass,s.upper[0],s.upper[1],s.upper[2],2,dx,inset,contact_distance};write_bytes(constants,sizeof(constants));
    write_bytes(s.wall.data(),s.wall.size()*sizeof(V));
    Search walls(s.upper);walls.build(s.wall);
    Search fluid(s.upper),contacts(s.upper);
    auto save=[&](unsigned step) {
        std::uint32_t id=step;write_bytes(&id,sizeof(id));write_bytes(s.p.data(),n*sizeof(V));write_bytes(s.v.data(),n*sizeof(V));std::cout.flush();
    };save(0);
    std::vector<V> old,predicted,owner(n),correction(n);std::vector<double> lambda(n),rho(n);
    std::vector<std::vector<unsigned>> rows(n),wall_rows(n);
    double worst_residual=0,solver_s=0;
    std::atomic<bool> nonfinite{false};
    for(unsigned step=1;step<=steps;++step) {
        const auto begin=std::chrono::steady_clock::now();
        old=s.p;predicted=s.p;
        if(nonfinite)throw std::runtime_error("nonfinite candidate");
        for(unsigned i=0;i<n;++i) {s.v[i][1]-=9.81*dt;predicted[i]=add(old[i],mul(s.v[i],dt));}
        for(unsigned it=0;it<iterations;++it) {
            if(it==0 || refresh) {
                fluid.build(predicted);
                #pragma omp parallel for schedule(static)
                for(unsigned i=0;i<n;++i) {rows[i]=fluid.row(predicted[i]);wall_rows[i]=boundary ? walls.row(predicted[i]) : std::vector<unsigned>{};}
            }
            #pragma omp parallel for schedule(static)
            for(unsigned i=0;i<n;++i) {
                double density=weight(0),squared=0;V sum{};
                for(unsigned j:rows[i])if(j!=i) {
                    V d=sub(predicted[i],predicted[j]);density+=weight(dot(d,d));
                    V g=mul(gradient(d,poly),1/rest);sum=add(sum,g);squared+=dot(g,g);
                }
                for(unsigned j:wall_rows[i]) {
                    V d=sub(predicted[i],s.wall[j]);density+=weight(dot(d,d));sum=add(sum,mul(gradient(d,poly),1/rest));
                }
                owner[i]=sum;rho[i]=density;double c=density/rest-1;
                lambda[i]=-(clamp ? std::max(0.,c) : c)/(squared+dot(sum,sum)+eps);
            }
            // Fluid rows are reciprocal; the sum is the transpose constraint
            // action. Fixed samples contribute only to the owner's direction.
            #pragma omp parallel for schedule(static)
            for(unsigned i=0;i<n;++i) {
                V delta=mul(owner[i],lambda[i]);
                for(unsigned j:rows[i])if(j!=i) {
                    V d=sub(predicted[i],predicted[j]);const double scorr=0;
                    delta=add(delta,mul(gradient(d,poly),(lambda[j]+scorr)/rest));
                }
                correction[i]=mul(delta,scale);
            }
            #pragma omp parallel for schedule(static)
            for(unsigned i=0;i<n;++i) {
                predicted[i]=add(predicted[i],correction[i]);
                for(unsigned k=0;k<3;++k) {
                    if(!std::isfinite(predicted[i][k]))nonfinite=true;
                    predicted[i][k]=std::clamp(predicted[i][k],inset,s.upper[k]-inset);
                }
            }
            if(contact) {
                contacts.build(predicted);
                #pragma omp parallel for schedule(static)
                for(unsigned i=0;i<n;++i) {
                    V delta{};
                    for(unsigned j:contacts.row(predicted[i]))if(i!=j) {
                        V d=sub(predicted[i],predicted[j]);double r=std::sqrt(dot(d,d));
                        if(r<contact_distance) {
                            if(r==0) {d={};d[(i+j)%3]=i<j ? 1 : -1;}
                            else d=mul(d,1/r);
                            delta=add(delta,mul(d,(contact_distance-r)*.5));
                        }
                    }
                    correction[i]=delta;
                }
                #pragma omp parallel for schedule(static)
                for(unsigned i=0;i<n;++i) {
                    predicted[i]=add(predicted[i],correction[i]);
                    for(unsigned k=0;k<3;++k)predicted[i][k]=std::clamp(predicted[i][k],inset,s.upper[k]-inset);
                }
            }
        }
        if(nonfinite)throw std::runtime_error("nonfinite candidate");
        for(unsigned i=0;i<n;++i) {s.v[i]=mul(sub(predicted[i],old[i]),1/dt);worst_residual=std::max(worst_residual,rho[i]/rest-1);}
        s.p=predicted;
        solver_s+=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
        if(step%stride==0 || step==steps)save(step);
    }
    std::cerr<<std::setprecision(17)<<"{\"completed_steps\":"<<steps<<",\"particles\":"<<n
        <<",\"solver_s\":"<<solver_s<<",\"threads\":"<<threads
        <<",\"last_iteration_input_max_compression_over_run\":"<<worst_residual<<"}\n";
    return 0;
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
