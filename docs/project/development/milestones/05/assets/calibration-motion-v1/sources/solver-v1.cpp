// Isolated calibration and energy-ledger experiments preserve the spatial
// reference arithmetic in raw mode. Every solver stage records its actual work;
// viscosity is a dimensional Newtonian material model, never a quietness fit.
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
#include <limits>
#include "qualification_viscosity.hpp"

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
static Scene scene(std::string name,int n,double layers,double inset) {
    Scene s;s.upper={1.2,1.2,.8};
    const bool fitted=name.size()>6 && name.substr(name.size()-6)=="-valid";
    if(fitted)name.resize(name.size()-6);
    auto sample=[&](V lower,V extent,std::array<int,3> count,V velocity) {
        for(int x=0;x<count[0];++x)for(int y=0;y<count[1];++y)for(int z=0;z<count[2];++z) {
            V p{};const int index[]={x,y,z};
            for(unsigned k=0;k<3;++k) {
                const double margin=std::max(extent[k]/(2*count[k]),inset);
                if(fitted && count[k]>1) p[k]=lower[k]+margin+(extent[k]-2*margin)*index[k]/(count[k]-1);
                else p[k]=lower[k]+extent[k]*(index[k]+.5)/count[k];
            }
            s.p.push_back(p);s.v.push_back(velocity);
        }
    };
    if(name=="tank")sample({0,0,0},{1.2,.3,.8},{4*n,n,8*n/3},{});
    else if(name=="collision") {
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

struct Energy {
    double k=0,u=0;V momentum{},angular{};
};
static V cross(V a,V b) {return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
static Energy energy(const std::vector<V> &p,const std::vector<V> &v,double gravity) {
    Energy e;for(unsigned i=0;i<p.size();++i) {e.k+=dot(v[i],v[i])*.5;e.u+=gravity*p[i][1];e.momentum=add(e.momentum,v[i]);e.angular=add(e.angular,cross(p[i],v[i]));}
    const double inv=1./p.size();e.k*=inv;e.u*=inv;e.momentum=mul(e.momentum,inv);e.angular=mul(e.angular,inv);return e;
}
static Energy effective(const std::vector<V> &p,const std::vector<V> &old,double dt,double gravity) {
    std::vector<V> v(p.size());for(unsigned i=0;i<p.size();++i)v[i]=mul(sub(p[i],old[i]),1/dt);return energy(p,v,gravity);
}
struct Work {
    double dk=0,du=0,positive=0,negative=0,displacement2=0,max_displacement=0;V impulse{},angular{};unsigned active=0;
    void add_stage(Energy before,Energy after,const std::vector<V> &delta) {
        dk+=after.k-before.k;du+=after.u-before.u;const double de=after.k+after.u-before.k-before.u;
        positive+=std::max(0.,de);negative+=std::min(0.,de);
        impulse=add(impulse,sub(after.momentum,before.momentum));angular=add(angular,sub(after.angular,before.angular));
        for(V d:delta) {double r2=dot(d,d);displacement2+=r2;max_displacement=std::max(max_displacement,std::sqrt(r2));if(r2>0)++active;}
    }
};
static void vector_json(std::ostream &o,V v) {o<<"["<<v[0]<<","<<v[1]<<","<<v[2]<<"]";}
static void state_json(std::ostream &o,Energy e) {
    o<<"{\"K\":"<<e.k<<",\"U\":"<<e.u<<",\"mean_v\":";vector_json(o,e.momentum);o<<",\"angular_per_kg\":";vector_json(o,e.angular);o<<"}";
}
static void work_json(std::ostream &o,const Work &w,unsigned n) {
    o<<"{\"dK\":"<<w.dk<<",\"dU\":"<<w.du<<",\"positive_dE\":"<<w.positive<<",\"negative_dE\":"<<w.negative<<",\"displacement_rms_sum\":"<<std::sqrt(w.displacement2/n)<<",\"max_displacement\":"<<w.max_displacement<<",\"active_particle_stages\":"<<w.active<<",\"impulse_per_kg\":";vector_json(o,w.impulse);o<<",\"angular_impulse_per_kg\":";vector_json(o,w.angular);o<<"}";
}

int main(int argc,char **argv) try {
    if(argc!=20)throw std::runtime_error("scene n layers dt duration iterations boundary inset_fraction threads calibration wall_volume nu contact density gravity ledger restart velocity_factor support");
    const std::string name=argv[1];const int resolution=std::stoi(argv[2]);const double layers=std::stod(argv[3]);
    const double dt=std::stod(argv[4]),duration=std::stod(argv[5]);
    const unsigned iterations=std::stoul(argv[6]);const bool boundary=std::stoi(argv[7]);
    const double inset_fraction=std::stod(argv[8]);const int threads=std::stoi(argv[9]);
    if(!(resolution>=6 && resolution<=36 && resolution%6==0 && layers>=1 && layers<=24 && dt>0 && dt<=.02 && duration>=0 && duration<=12 && duration/dt<=100000 && iterations>0 && iterations<=128 && inset_fraction>=0 && inset_fraction<=.5 && threads>0 && threads<=24))
        throw std::runtime_error("invalid spatial request");
    const std::string calibration=argv[10];const bool physical_wall=std::stoi(argv[11]);
    const double nu=std::stod(argv[12]);const bool contact=std::stoi(argv[13]),density_enabled=std::stoi(argv[14]);
    const double gravity=std::stod(argv[15]);const std::string ledger_path=argv[16],restart=argv[17];
    const double velocity_factor=std::stod(argv[18]),support_ratio=std::stod(argv[19]);
    if((calibration!="raw" && calibration!="self" && calibration!="ratio") || !(nu>=0 && nu<=.01 && gravity>=0 && gravity<=10 && velocity_factor>=0 && velocity_factor<=1 && support_ratio>=2 && support_ratio<=4))throw std::runtime_error("invalid physical-model request");
    dx=.3/resolution;h=support_ratio*dx;w_coefficient=21/(2*pi*h*h*h);g_coefficient=-20*w_coefficient/(h*h);
    const double base_mass=1000/8270.744069418484;
    const double mass=base_mass*216/std::pow(resolution,3),rest=1000/mass;
    const double eps=.02/(h*h),scale=.5,inset=inset_fraction*dx,contact_distance=.51*dx;
    const bool clamp=true,poly=true,refresh=true;
    const double ell=std::cbrt(mass/1000);double lattice=0;
    const int extent=static_cast<int>(std::ceil(h/ell));
    for(int x=-extent;x<=extent;++x)for(int y=-extent;y<=extent;++y)for(int z=-extent;z<=extent;++z)
        lattice+=weight(ell*ell*(x*x+y*y+z*z));
    const double bias=lattice-rest,ratio=calibration=="ratio" ? lattice/rest : 1;
    const double subtract_bias=calibration=="self" ? bias : 0;
    const double wall_multiplier=physical_wall ? 1000*dx*dx*dx/mass : 1;
    std::ofstream ledger(ledger_path);if(!ledger)throw std::runtime_error("cannot open energy ledger");
    ledger<<std::setprecision(17);
    omp_set_dynamic(0);omp_set_num_threads(threads);
    Scene s=scene(name,resolution,layers,inset);const unsigned n=s.p.size();
    if(restart!="-") {
        std::ifstream input(restart,std::ios::binary);std::uint32_t count=0;
        input.read(reinterpret_cast<char*>(&count),4);
        if(count!=n)throw std::runtime_error("restart count differs");
        input.read(reinterpret_cast<char*>(s.p.data()),n*sizeof(V));input.read(reinterpret_cast<char*>(s.v.data()),n*sizeof(V));
        if(!input || input.peek()!=std::ifstream::traits_type::eof())throw std::runtime_error("invalid restart arrays");
    }
    for(auto &v:s.v)v=mul(v,velocity_factor);
    const unsigned steps=std::lround(duration/dt),stride=std::max(1L,std::lround(.05/dt));
    const std::uint32_t header[]={0x50424634U,n,static_cast<unsigned>(s.wall.size()),steps};write_bytes(header,sizeof(header));
    const double constants[]={dt,h,rest,mass,s.upper[0],s.upper[1],s.upper[2],2,dx,inset,contact_distance};write_bytes(constants,sizeof(constants));
    write_bytes(s.wall.data(),s.wall.size()*sizeof(V));
    Search walls(s.upper);walls.build(s.wall);
    Search fluid(s.upper),contacts(s.upper);
    auto save=[&](unsigned step) {
        std::uint32_t id=step;write_bytes(&id,sizeof(id));write_bytes(s.p.data(),n*sizeof(V));write_bytes(s.v.data(),n*sizeof(V));std::cout.flush();
    };save(0);
    if(name.size()>6 && name.substr(name.size()-6)=="-valid") {
        Search initial(s.upper);initial.build(s.p);
        for(unsigned i=0;i<n;++i) {
            for(unsigned k=0;k<3;++k)if(s.p[i][k]<inset-1e-12 || s.p[i][k]>s.upper[k]-inset+1e-12)
                throw std::runtime_error("initial centre violates collision inset");
            for(unsigned j:initial.row(s.p[i]))if(j>i) {
                V d=sub(s.p[i],s.p[j]);
                if(std::sqrt(dot(d,d))<contact_distance-1e-12)throw std::runtime_error("initial separation violates distance target");
            }
        }
    }
    std::vector<V> old,predicted,owner(n),correction(n),free_prediction,delta(n),velocity_before;std::vector<double> lambda(n),rho(n);
    std::vector<std::vector<unsigned>> rows(n),wall_rows(n);
    double worst_residual=0,solver_s=0;
    std::atomic<bool> nonfinite{false};
    for(unsigned step=1;step<=steps;++step) {
        const auto begin=std::chrono::steady_clock::now();
        old=s.p;predicted=s.p;const Energy initial_energy=energy(s.p,s.v,gravity);
        Work density_work,plane_work,contact_work,viscous_work;unsigned active_density=0,wall_neighbours=0;
        V wall_density_displacement{};double max_viscous_row=0;
        if(nonfinite)throw std::runtime_error("nonfinite candidate");
        for(unsigned i=0;i<n;++i) {s.v[i][1]-=gravity*dt;predicted[i]=add(old[i],mul(s.v[i],dt));}
        free_prediction=predicted;const Energy prediction_energy=effective(predicted,old,dt,gravity);
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
                    V d=sub(predicted[i],s.wall[j]);density+=wall_multiplier*weight(dot(d,d));sum=add(sum,mul(gradient(d,poly),wall_multiplier/rest));
                }
                density=(density-subtract_bias)/ratio;sum=mul(sum,1/ratio);squared/=ratio*ratio;
                owner[i]=sum;rho[i]=density;double c=density/rest-1;
                lambda[i]=density_enabled ? -(clamp ? std::max(0.,c) : c)/(squared+dot(sum,sum)+eps) : 0;
            }
            // Fluid rows are reciprocal; the sum is the transpose constraint
            // action. Fixed samples contribute only to the owner's direction.
            #pragma omp parallel for schedule(static)
            for(unsigned i=0;i<n;++i) {
                V delta=mul(owner[i],lambda[i]);
                for(unsigned j:rows[i])if(j!=i) {
                    V d=sub(predicted[i],predicted[j]);const double scorr=0;
                    delta=add(delta,mul(gradient(d,poly),(lambda[j]+scorr)/(rest*ratio)));
                }
                correction[i]=mul(delta,scale);
            }
            for(unsigned i=0;i<n;++i) {
                if(lambda[i]!=0)++active_density;
                wall_neighbours+=wall_rows[i].size();
                V wall_sum{};for(unsigned j:wall_rows[i])wall_sum=add(wall_sum,mul(gradient(sub(predicted[i],s.wall[j]),poly),wall_multiplier/(rest*ratio)));
                wall_density_displacement=add(wall_density_displacement,mul(wall_sum,lambda[i]*scale));
            }
            Energy before=effective(predicted,old,dt,gravity);
            for(unsigned i=0;i<n;++i) {predicted[i]=add(predicted[i],correction[i]);for(double q:predicted[i])if(!std::isfinite(q))nonfinite=true;}
            density_work.add_stage(before,effective(predicted,old,dt,gravity),correction);
            before=effective(predicted,old,dt,gravity);
            for(unsigned i=0;i<n;++i) {V previous=predicted[i];for(unsigned k=0;k<3;++k)predicted[i][k]=std::clamp(predicted[i][k],inset,s.upper[k]-inset);delta[i]=sub(predicted[i],previous);}
            plane_work.add_stage(before,effective(predicted,old,dt,gravity),delta);
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
                before=effective(predicted,old,dt,gravity);
                for(unsigned i=0;i<n;++i)predicted[i]=add(predicted[i],correction[i]);
                contact_work.add_stage(before,effective(predicted,old,dt,gravity),correction);
                before=effective(predicted,old,dt,gravity);
                for(unsigned i=0;i<n;++i) {V previous=predicted[i];for(unsigned k=0;k<3;++k)predicted[i][k]=std::clamp(predicted[i][k],inset,s.upper[k]-inset);delta[i]=sub(predicted[i],previous);}
                plane_work.add_stage(before,effective(predicted,old,dt,gravity),delta);
            }
        }
        if(nonfinite)throw std::runtime_error("nonfinite candidate");
        for(unsigned i=0;i<n;++i) {s.v[i]=mul(sub(predicted[i],old[i]),1/dt);worst_residual=std::max(worst_residual,rho[i]/rest-1);}
        double reconstruction_error=0;
        for(unsigned i=0;i<n;++i) {V reference=add(mul(sub(free_prediction[i],old[i]),1/dt),mul(sub(predicted[i],free_prediction[i]),1/dt));reconstruction_error=std::max(reconstruction_error,std::sqrt(dot(sub(reference,s.v[i]),sub(reference,s.v[i]))));}
        const Energy reconstructed=energy(predicted,s.v,gravity);
        if(nu>0) {
            velocity_before=s.v;fluid.build(predicted);const double volume=mass/1000;
            #pragma omp parallel for schedule(static)
            for(unsigned i=0;i<n;++i) {
                V change{};double row=0;
                for(unsigned j:fluid.row(predicted[i]))if(j!=i) {
                    const auto pair=qualification::viscous_pair(sub(predicted[i],predicted[j]),sub(velocity_before[j],velocity_before[i]),h,nu,volume);
                    change=add(change,pair.acceleration);row+=pair.row;
                }
                correction[i]=mul(change,dt);rho[i]=row*dt;
            }
            for(unsigned i=0;i<n;++i) {max_viscous_row=std::max(max_viscous_row,rho[i]);s.v[i]=add(velocity_before[i],correction[i]);delta[i]={};}
            if(max_viscous_row>1)throw std::runtime_error("explicit viscous row bound exceeded");
            viscous_work.add_stage(reconstructed,energy(predicted,s.v,gravity),delta);
        }
        const Energy accepted=energy(predicted,s.v,gravity);
        ledger<<"{\"step\":"<<step<<",\"time\":"<<step*dt<<",\"initial\":";state_json(ledger,initial_energy);
        ledger<<",\"prediction\":";state_json(ledger,prediction_energy);ledger<<",\"reconstructed\":";state_json(ledger,reconstructed);ledger<<",\"accepted\":";state_json(ledger,accepted);
        ledger<<",\"density\":";work_json(ledger,density_work,n);ledger<<",\"plane\":";work_json(ledger,plane_work,n);ledger<<",\"contact\":";work_json(ledger,contact_work,n);ledger<<",\"viscosity\":";work_json(ledger,viscous_work,n);
        ledger<<",\"active_density_constraints\":"<<active_density<<",\"wall_neighbour_stages\":"<<wall_neighbours<<",\"density_wall_impulse_per_kg\":";vector_json(ledger,mul(wall_density_displacement,1/(n*dt)));
        ledger<<",\"reconstruction_error_m_s\":"<<reconstruction_error<<",\"max_viscous_row_dt\":"<<max_viscous_row<<"}\n";
        if(!ledger)throw std::runtime_error("ledger write failed");
        s.p=predicted;
        solver_s+=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
        if(step%stride==0 || step==steps)save(step);
    }
    std::cerr<<std::setprecision(17)<<"{\"completed_steps\":"<<steps<<",\"particles\":"<<n
        <<",\"solver_s\":"<<solver_s<<",\"threads\":"<<threads
        <<",\"calibration_bias_kg_m3\":"<<mass*bias<<",\"calibration_ratio\":"<<lattice/rest<<",\"wall_mass_multiplier\":"<<wall_multiplier<<",\"last_iteration_input_max_compression_over_run\":"<<worst_residual<<"}\n";
    return 0;
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
