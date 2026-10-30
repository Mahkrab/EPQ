// Disposable binary64 PBF experiment: fixed volumetric wall samples and fluid
// constraints share a kernel sum, but fixed samples own no constraint or motion.
// Production backends and retained optimisations are not modified by this tool.
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

using V=std::array<double,3>;
using Cell=std::array<int,3>;
static V add(V a,V b) {for(unsigned k=0;k<3;++k)a[k]+=b[k];return a;}
static V sub(V a,V b) {for(unsigned k=0;k<3;++k)a[k]-=b[k];return a;}
static V mul(V a,double b) {for(double &v:a)v*=b;return a;}
static double dot(V a,V b) {double s=0;for(unsigned k=0;k<3;++k)s+=a[k]*b[k];return s;}
constexpr double dx=.05,h=.1,pi=3.14159265358979323846;
static double weight(double r2) {return r2<h*h ? 315/(64*pi*std::pow(h,9))*std::pow(h*h-r2,3) : 0;}
static V gradient(V d,bool poly) {
    double r2=dot(d,d);if(r2==0 || r2>=h*h)return {};
    if(poly)return mul(d,-6*315/(64*pi*std::pow(h,9))*std::pow(h*h-r2,2));
    double r=std::sqrt(r2);return mul(d,-45/(pi*std::pow(h,6))*(h-r)*(h-r)/r);
}
static double rest_density() {
    double value=0;
    for(int x=-2;x<=2;++x)for(int y=-2;y<=2;++y)for(int z=-2;z<=2;++z)
        value+=weight(dx*dx*(x*x+y*y+z*z));
    return value;
}
struct Scene {std::vector<V> p,v,wall;V upper;};
static Scene scene(const std::string &name) {
    Scene s;s.upper={.4,.8,.4};
    auto block=[&](V origin,std::array<int,3> count,V velocity) {
        for(int x=0;x<count[0];++x)for(int y=0;y<count[1];++y)for(int z=0;z<count[2];++z) {
            s.p.push_back(add(origin,{dx*x,dx*y,dx*z}));s.v.push_back(velocity);
        }
    };
    if(name=="hydro")block({.025,.025,.025},{8,8,8},{});
    else if(name=="hydro-large") {s.upper={1,1,1};block({.025,.025,.025},{20,8,20},{});}
    else if(name=="fall") {s.upper={.8,1.2,.8};block({.225,.625,.225},{8,8,8},{});}
    else if(name=="collision") {
        s.upper={1.2,1.2,.8};block({.125,.4,.225},{6,6,6},{.5,0,0});
        block({.825,.4,.225},{6,6,6},{-.5,0,0});
    } else if(name=="ballistic") {s.upper={10,10,10};block({4,7,4},{4,4,4},{});}
    else throw std::runtime_error("unknown scene");
    // Two half-offset layers fill the kernel support outside every box face;
    // edge and corner cells are included once, so wall volume is not doubled.
    std::array<int,3> cells{};for(unsigned k=0;k<3;++k)cells[k]=std::lround(s.upper[k]/dx);
    if(name!="ballistic")for(int x=-2;x<cells[0]+2;++x)for(int y=-2;y<cells[1]+2;++y)for(int z=-2;z<cells[2]+2;++z)
        if(x<0 || y<0 || z<0 || x>=cells[0] || y>=cells[1] || z>=cells[2])
            s.wall.push_back({dx*(x+.5),dx*(y+.5),dx*(z+.5)});
    return s;
}
struct Search {
    std::map<Cell,std::vector<unsigned>> grid;
    const std::vector<V> *positions=nullptr;
    static Cell cell(V p) {return {int(std::floor(p[0]/h)),int(std::floor(p[1]/h)),int(std::floor(p[2]/h))};}
    void build(const std::vector<V> &p) {positions=&p;grid.clear();for(unsigned i=0;i<p.size();++i)grid[cell(p[i])].push_back(i);}
    std::vector<unsigned> row(V p) const {
        std::vector<unsigned> result;auto c=cell(p);
        for(int x=-1;x<=1;++x)for(int y=-1;y<=1;++y)for(int z=-1;z<=1;++z) {
            auto it=grid.find({c[0]+x,c[1]+y,c[2]+z});
            if(it!=grid.end())for(auto j:it->second) {
                V d=sub(p,(*positions)[j]);if(dot(d,d)<h*h)result.push_back(j);
            }
        }
        std::sort(result.begin(),result.end());return result;
    }
};
static void write_bytes(const void *p,std::size_t n) {std::cout.write(static_cast<const char *>(p),n);if(!std::cout)throw std::runtime_error("observation write failed");}

int main(int argc,char **argv) try {
    if(argc!=12)throw std::runtime_error("scene dt duration iterations boundary clamp epsilon_h2 scale pressure_h2 poly refresh");
    const std::string name=argv[1];const double dt=std::stod(argv[2]),duration=std::stod(argv[3]);
    const unsigned iterations=std::stoul(argv[4]);const bool boundary=std::stoi(argv[5]),clamp=std::stoi(argv[6]);
    const double eps=std::stod(argv[7])/(h*h),scale=std::stod(argv[8]),pressure=std::stod(argv[9])*h*h;
    const bool poly=std::stoi(argv[10]),refresh=std::stoi(argv[11]);
    if(!(dt>0 && duration>=0 && duration<=10 && iterations>0 && iterations<=256 && eps>0 && scale>0 && scale<=1 && pressure>=0))
        throw std::runtime_error("parameters exceed bounded experiment");
    Scene s=scene(name);const unsigned n=s.p.size(),steps=std::lround(duration/dt),stride=std::max(1L,std::lround(.05/dt));
    const double rest=rest_density(),mass=1000/rest;
    const std::uint32_t header[]={0x50424632,n,static_cast<unsigned>(s.wall.size()),steps};write_bytes(header,sizeof(header));
    const double constants[]={dt,h,rest,mass,s.upper[0],s.upper[1],s.upper[2]};write_bytes(constants,sizeof(constants));
    write_bytes(s.wall.data(),s.wall.size()*sizeof(V));
    Search walls;walls.build(s.wall);
    auto save=[&](unsigned step) {
        std::uint32_t id=step;write_bytes(&id,sizeof(id));write_bytes(s.p.data(),n*sizeof(V));write_bytes(s.v.data(),n*sizeof(V));std::cout.flush();
    };save(0);
    std::vector<V> old,predicted,owner(n),correction(n);std::vector<double> lambda(n),rho(n);
    std::vector<std::vector<unsigned>> rows(n),wall_rows(n);
    double worst_residual=0;
    for(unsigned step=1;step<=steps;++step) {
        old=s.p;predicted=s.p;
        for(unsigned i=0;i<n;++i) {s.v[i][1]-=9.81*dt;predicted[i]=add(old[i],mul(s.v[i],dt));}
        Search fluid;
        for(unsigned it=0;it<iterations;++it) {
            if(it==0 || refresh) {
                fluid.build(predicted);
                for(unsigned i=0;i<n;++i) {rows[i]=fluid.row(predicted[i]);wall_rows[i]=boundary ? walls.row(predicted[i]) : std::vector<unsigned>{};}
            }
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
            for(unsigned i=0;i<n;++i) {
                V delta=mul(owner[i],lambda[i]);
                for(unsigned j:rows[i])if(j!=i) {
                    V d=sub(predicted[i],predicted[j]);double r2=dot(d,d);
                    double scorr=-pressure*std::pow(weight(r2)/weight(.04*h*h),4);
                    delta=add(delta,mul(gradient(d,poly),(lambda[j]+scorr)/rest));
                }
                correction[i]=mul(delta,scale);
            }
            for(unsigned i=0;i<n;++i) {
                predicted[i]=add(predicted[i],correction[i]);
                for(unsigned k=0;k<3;++k) {
                    if(!std::isfinite(predicted[i][k]))throw std::runtime_error("nonfinite candidate");
                    predicted[i][k]=std::clamp(predicted[i][k],0.,s.upper[k]);
                }
            }
        }
        for(unsigned i=0;i<n;++i) {s.v[i]=mul(sub(predicted[i],old[i]),1/dt);worst_residual=std::max(worst_residual,rho[i]/rest-1);}
        s.p=predicted;if(step%stride==0 || step==steps)save(step);
    }
    std::cerr<<"{\"completed_steps\":"<<steps<<",\"particles\":"<<n<<",\"last_iteration_input_max_compression_over_run\":"<<worst_residual<<"}\n";
    return 0;
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
