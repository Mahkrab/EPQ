// Reflected-fluid density support and its full Jacobian couple pressure to
// dimensional edge-strain viscosity. Raw states and every accepted stage remain
// independent of production code and include the physical wall reactions.
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
#include "traction_viscosity.hpp"

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
static V domain{.2,.1,.2};
static V separation(V a,V b) {
    V d=sub(a,b);for(unsigned k:{0U,2U})d[k]-=std::round(d[k]/domain[k])*domain[k];return d;
}
static Scene scene(std::string name,int ny,double amplitude,double inset) {
    (void)inset;Scene s;s.upper=domain;const int nx=4*ny;
    for(int x=0;x<nx;++x)for(int y=0;y<ny;++y)for(int z=0;z<nx;++z) {
        V p{dx*(x+.5),dx*(y+.5),dx*(z+.5)},v{};
        if(name=="channel-mixed")v[0]=amplitude*std::sin(pi*p[1]/.1);
        else if(name=="channel-horizontal")v[0]=amplitude*std::sin(2*pi*p[2]/.2);
        else if(name!="channel-rest")throw std::runtime_error("unknown channel");
        s.p.push_back(p);s.v.push_back(v);
    }
    for(int x=0;x<nx;++x)for(int z=0;z<nx;++z)for(int y=0;y<2;++y) {
        s.wall.push_back({dx*(x+.5),-dx*(y+.5),dx*(z+.5)});
        s.wall.push_back({dx*(x+.5),domain[1]+dx*(y+.5),dx*(z+.5)});
    }
    return s;
}
struct Search {
    double radius;
    std::array<int,3> dims; V width;
    std::vector<std::vector<unsigned>> bins;
    const std::vector<V> *positions=nullptr;
    explicit Search(V upper,double support=h):radius(support) {
        for(unsigned k=0;k<3;++k) {if(k!=1) {dims[k]=int(std::floor(upper[k]/radius));width[k]=upper[k]/dims[k];if(dims[k]<3)throw std::runtime_error("periodic channel too narrow");}else {dims[k]=int(std::ceil(upper[k]/radius))+6;width[k]=radius;}}
        bins.resize(static_cast<std::size_t>(dims[0])*dims[1]*dims[2]);
    }
    Cell cell(V p) const {Cell c;for(unsigned k=0;k<3;++k) {if(k!=1)p[k]-=std::floor(p[k]/domain[k])*domain[k];c[k]=int(std::floor(p[k]/width[k]))+(k==1 ? 3 : 0);if(k!=1)c[k]=std::min(c[k],dims[k]-1);}return c;}
    std::size_t key(Cell c) const {return (static_cast<std::size_t>(c[0])*dims[1]+c[1])*dims[2]+c[2];}
    bool valid(Cell c) const {return c[0]>=0 && c[1]>=0 && c[2]>=0 && c[0]<dims[0] && c[1]<dims[1] && c[2]<dims[2];}
    void build(const std::vector<V> &p) {
        positions=&p;for(auto &b:bins)b.clear();
        for(unsigned i=0;i<p.size();++i) {auto c=cell(p[i]);if(!valid(c))throw std::runtime_error("search bounds exceeded");bins[key(c)].push_back(i);}
    }
    std::vector<unsigned> row(V p) const {
        std::vector<unsigned> result;auto c=cell(p);
        for(int x=-1;x<=1;++x)for(int y=-1;y<=1;++y)for(int z=-1;z<=1;++z) {
            Cell q{(c[0]+x+dims[0])%dims[0],c[1]+y,(c[2]+z+dims[2])%dims[2]};if(!valid(q))continue;
            for(auto j:bins[key(q)]) {V d=separation(p,(*positions)[j]);if(dot(d,d)<radius*radius)result.push_back(j);}
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
    if(argc!=22)throw std::runtime_error("scene n layers dt duration iterations boundary inset_fraction threads calibration wall_volume nu contact density gravity ledger restart velocity_factor support");
    const std::string name=argv[1];const int resolution=std::stoi(argv[2]);const double layers=std::stod(argv[3]);
    const double dt=std::stod(argv[4]),duration=std::stod(argv[5]);
    const unsigned iterations=std::stoul(argv[6]);const bool boundary=std::stoi(argv[7]);
    const double inset_fraction=std::stod(argv[8]);const int threads=std::stoi(argv[9]);
    if(!(resolution>=4 && resolution<=24 && layers>=0 && layers<=1 && dt>0 && dt<=.02 && duration>=0 && duration<=12 && duration/dt<=100000 && iterations>0 && iterations<=128 && inset_fraction>=0 && inset_fraction<=.5 && threads>0 && threads<=24))
        throw std::runtime_error("invalid spatial request");
    const std::string calibration=argv[10];const bool physical_wall=std::stoi(argv[11]);
    const double nu=std::stod(argv[12]);const bool contact=std::stoi(argv[13]),density_enabled=std::stoi(argv[14]);
    const double gravity=std::stod(argv[15]);const std::string ledger_path=argv[16],restart=argv[17];
    const double velocity_factor=std::stod(argv[18]),support_ratio=std::stod(argv[19]);
    const double viscosity_support=(argc>=21 ? std::stod(argv[20]) : 2)*(.05/resolution);
    if(!(viscosity_support>=2*(.05/resolution) && viscosity_support<=4*(.05/resolution)))throw std::runtime_error("invalid viscosity support");
    if((calibration!="raw" && calibration!="self" && calibration!="ratio") || !(nu>=0 && nu<=.01 && gravity>=0 && gravity<=10 && velocity_factor>=0 && velocity_factor<=1 && support_ratio>=2 && support_ratio<=4))throw std::runtime_error("invalid physical-model request");
    dx=.05/resolution;h=support_ratio*dx;w_coefficient=21/(2*pi*h*h*h);g_coefficient=-20*w_coefficient/(h*h);
    const double base_mass=1000/8270.744069418484;
    const std::string mass_scheme=argc==22 ? argv[21] : "inherited";
    if(mass_scheme!="inherited" && mass_scheme!="geometric")throw std::runtime_error("invalid mass convention");
    const double mass=mass_scheme=="geometric" ? 1000*dx*dx*dx : base_mass*216/std::pow(resolution,3),rest=1000/mass;
    const double eps=.02/(h*h),scale=.5,inset=inset_fraction*dx,contact_distance=.51*dx;
    const bool poly=true,refresh=true;
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
    Search fluid(s.upper),contacts(s.upper),reflected(s.upper);
    std::vector<V> images;std::vector<unsigned> targets;
    std::vector<std::vector<std::pair<unsigned,V>>> jacobian(n);
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
        V wall_density_displacement{};double max_viscous_row=0,physical_loss=0,temporal_loss=0,cg_residual=0,condition=0;unsigned cg_iterations=0;
        if(nonfinite)throw std::runtime_error("nonfinite candidate");
        for(unsigned i=0;i<n;++i) {s.v[i][1]-=gravity*dt;predicted[i]=add(old[i],mul(s.v[i],dt));}
        free_prediction=predicted;const Energy prediction_energy=effective(predicted,old,dt,gravity);
        for(unsigned it=0;it<iterations;++it) {
            if(it==0 || refresh) {
                fluid.build(predicted);images.clear();targets.clear();
                if(boundary)for(unsigned j=0;j<n;++j)for(int side=0;side<2;++side) {
                    const double plane=side ? s.upper[1] : 0;
                    if(std::abs(predicted[j][1]-plane)<h) {V p=predicted[j];p[1]=2*plane-p[1];images.push_back(p);targets.push_back(j);}
                }
                reflected.build(images);
                #pragma omp parallel for schedule(static)
                for(unsigned i=0;i<n;++i) {rows[i]=fluid.row(predicted[i]);wall_rows[i]=boundary ? reflected.row(predicted[i]) : std::vector<unsigned>{};}
            }
            #pragma omp parallel for schedule(static)
            for(unsigned i=0;i<n;++i) {
                double density=weight(0);std::map<unsigned,V> row;
                for(unsigned j:rows[i])if(j!=i) {
                    V d=separation(predicted[i],predicted[j]);density+=weight(dot(d,d));
                    V g=mul(gradient(d,poly),1/(rest*ratio));row[i]=add(row[i],g);row[j]=sub(row[j],g);
                }
                for(unsigned image:wall_rows[i]) {
                    V d=separation(predicted[i],images[image]);density+=wall_multiplier*weight(dot(d,d));
                    V g=mul(gradient(d,poly),wall_multiplier/(rest*ratio));row[i]=add(row[i],g);g[1]*=-1;row[targets[image]]=sub(row[targets[image]],g);
                }
                jacobian[i].assign(row.begin(),row.end());double squared=0;for(const auto &entry:jacobian[i])squared+=dot(entry.second,entry.second);
                density=(density-subtract_bias)/ratio;rho[i]=density;const double c=density/rest-1;
                lambda[i]=density_enabled ? -std::max(0.,c)/(squared+eps) : 0;
            }
            // A separately compiled probe exports the actual sparse Jacobian
            // for independent finite differences, without changing its action.
            #ifdef MAELSTROM_DUMP_PRESSURE_JACOBIAN
            if(step==1 && it==0) {
                std::ofstream probe(ledger_path+".jac",std::ios::binary);
                std::uint32_t count=n;probe.write(reinterpret_cast<const char*>(&count),4);
                for(unsigned i=0;i<n;++i) {
                    double c=rho[i]/rest-1;std::uint32_t entries=jacobian[i].size();
                    probe.write(reinterpret_cast<const char*>(&c),8);probe.write(reinterpret_cast<const char*>(&lambda[i]),8);probe.write(reinterpret_cast<const char*>(&entries),4);
                    for(const auto &entry:jacobian[i]) {std::uint32_t target=entry.first;probe.write(reinterpret_cast<const char*>(&target),4);probe.write(reinterpret_cast<const char*>(entry.second.data()),24);}
                }
                if(!probe)throw std::runtime_error("Jacobian probe write failed");
            }
            #endif
            std::fill(correction.begin(),correction.end(),V{});
            for(unsigned i=0;i<n;++i) {
                if(lambda[i]!=0)++active_density;
                wall_neighbours+=wall_rows[i].size();
                for(const auto &entry:jacobian[i])correction[entry.first]=add(correction[entry.first],mul(entry.second,lambda[i]*scale));
            }
            for(V c:correction)wall_density_displacement[1]+=c[1];
            Energy before=effective(predicted,old,dt,gravity);
            for(unsigned i=0;i<n;++i) {predicted[i]=add(predicted[i],correction[i]);for(double q:predicted[i])if(!std::isfinite(q))nonfinite=true;}
            density_work.add_stage(before,effective(predicted,old,dt,gravity),correction);
            before=effective(predicted,old,dt,gravity);
            for(unsigned i=0;i<n;++i) {V previous=predicted[i];predicted[i][1]=std::clamp(predicted[i][1],inset,s.upper[1]-inset);delta[i]=sub(predicted[i],previous);}
            plane_work.add_stage(before,effective(predicted,old,dt,gravity),delta);
            if(contact) {
                contacts.build(predicted);
                #pragma omp parallel for schedule(static)
                for(unsigned i=0;i<n;++i) {
                    V delta{};
                    for(unsigned j:contacts.row(predicted[i]))if(i!=j) {
                        V d=separation(predicted[i],predicted[j]);double r=std::sqrt(dot(d,d));
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
                for(unsigned i=0;i<n;++i) {V previous=predicted[i];predicted[i][1]=std::clamp(predicted[i][1],inset,s.upper[1]-inset);delta[i]=sub(predicted[i],previous);}
                plane_work.add_stage(before,effective(predicted,old,dt,gravity),delta);
            }
        }
        if(nonfinite)throw std::runtime_error("nonfinite candidate");
        for(unsigned i=0;i<n;++i) {s.v[i]=mul(sub(predicted[i],old[i]),1/dt);worst_residual=std::max(worst_residual,rho[i]/rest-1);}
        double reconstruction_error=0;
        for(unsigned i=0;i<n;++i) {V reference=add(mul(sub(free_prediction[i],old[i]),1/dt),mul(sub(predicted[i],free_prediction[i]),1/dt));reconstruction_error=std::max(reconstruction_error,std::sqrt(dot(sub(reference,s.v[i]),sub(reference,s.v[i]))));}
        const Energy reconstructed=energy(predicted,s.v,gravity);
        if(nu>0) {
            velocity_before=s.v;
            traction::Operator op(predicted,s.upper,{true,false,true},{0,0,name=="channel-mixed" ? 2 : 1,0,0,0},viscosity_support);
            max_viscous_row=op.eigenvalue_bound(nu)*dt;condition=op.maximum_condition;
            std::vector<V> acceleration,residual(n),direction(n),action(n);op.apply(s.v,nu,acceleration);
            double rr=0,bnorm=0;
            for(unsigned i=0;i<n;++i) {residual[i]=mul(acceleration[i],dt);direction[i]=residual[i];rr+=dot(residual[i],residual[i]);bnorm+=dot(velocity_before[i],velocity_before[i]);}
            const double tolerance=std::max(1e-28,bnorm*1e-22);
            for(;rr>tolerance && cg_iterations<1000;++cg_iterations) {
                op.apply(direction,nu,acceleration);double denominator=0;
                for(unsigned i=0;i<n;++i) {action[i]=sub(direction[i],mul(acceleration[i],dt));denominator+=dot(direction[i],action[i]);}
                if(!(denominator>0))throw std::runtime_error("viscosity CG lost positive definiteness");
                const double alpha=rr/denominator;double next=0;
                for(unsigned i=0;i<n;++i) {s.v[i]=add(s.v[i],mul(direction[i],alpha));residual[i]=sub(residual[i],mul(action[i],alpha));next+=dot(residual[i],residual[i]);}
                for(unsigned i=0;i<n;++i)direction[i]=add(residual[i],mul(direction[i],next/rr));
                rr=next;
            }
            cg_residual=std::sqrt(rr/std::max(bnorm,1e-300));if(rr>tolerance)throw std::runtime_error("viscosity CG failed convergence");
            physical_loss=dt*op.apply(s.v,nu,acceleration);
            for(unsigned i=0;i<n;++i) {V dv=sub(s.v[i],velocity_before[i]);temporal_loss+=.5*dot(dv,dv)/n;delta[i]={};}
            viscous_work.add_stage(reconstructed,energy(predicted,s.v,gravity),delta);
        }
        const Energy accepted=energy(predicted,s.v,gravity);
        ledger<<"{\"step\":"<<step<<",\"time\":"<<step*dt<<",\"initial\":";state_json(ledger,initial_energy);
        ledger<<",\"prediction\":";state_json(ledger,prediction_energy);ledger<<",\"reconstructed\":";state_json(ledger,reconstructed);ledger<<",\"accepted\":";state_json(ledger,accepted);
        ledger<<",\"density\":";work_json(ledger,density_work,n);ledger<<",\"plane\":";work_json(ledger,plane_work,n);ledger<<",\"contact\":";work_json(ledger,contact_work,n);ledger<<",\"viscosity\":";work_json(ledger,viscous_work,n);
        ledger<<",\"active_density_constraints\":"<<active_density<<",\"wall_neighbour_stages\":"<<wall_neighbours<<",\"density_wall_impulse_per_kg\":";vector_json(ledger,mul(wall_density_displacement,1/(n*dt)));
        ledger<<",\"reconstruction_error_m_s\":"<<reconstruction_error<<",\"max_viscous_row_dt\":"<<max_viscous_row<<",\"physical_viscous_loss\":"<<physical_loss<<",\"viscous_time_loss\":"<<temporal_loss<<",\"cg_iterations\":"<<cg_iterations<<",\"cg_residual\":"<<cg_residual<<",\"gradient_condition\":"<<condition<<"}\n";
        if(!ledger)throw std::runtime_error("ledger write failed");
        s.p=predicted;for(auto &p:s.p)for(unsigned k:{0U,2U})p[k]-=std::floor(p[k]/domain[k])*domain[k];
        solver_s+=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
        if(step%stride==0 || step==steps)save(step);
    }
    std::cerr<<std::setprecision(17)<<"{\"completed_steps\":"<<steps<<",\"particles\":"<<n
        <<",\"solver_s\":"<<solver_s<<",\"threads\":"<<threads
        <<",\"calibration_bias_kg_m3\":"<<mass*bias<<",\"calibration_ratio\":"<<lattice/rest<<",\"wall_mass_multiplier\":"<<wall_multiplier<<",\"last_iteration_input_max_compression_over_run\":"<<worst_residual<<"}\n";
    return 0;
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
