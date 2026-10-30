// Newtonian strain energy is integrated at reconstructed neighbour edges.
// The exact velocity adjoint supplies forces, including solid mirror reactions.
// Natural fluid surfaces add no ghost mass or artificial damping coefficient.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>
#include <vector>
namespace traction {
using V=std::array<double,3>;using M=std::array<double,9>;
inline V plus(V a,V b) {for(int k=0;k<3;++k)a[k]+=b[k];return a;}
inline V minus(V a,V b) {for(int k=0;k<3;++k)a[k]-=b[k];return a;}
inline V times(V a,double s) {for(auto &x:a)x*=s;return a;}
inline double dot(V a,V b) {double s=0;for(int k=0;k<3;++k)s+=a[k]*b[k];return s;}
inline V mv(const M &a,V v) {V r{};for(int i=0;i<3;++i)for(int j=0;j<3;++j)r[i]+=a[3*i+j]*v[j];return r;}
inline double norminf(const M &m) {double result=0;for(int i=0;i<3;++i) {double s=0;for(int j=0;j<3;++j)s+=std::abs(m[3*i+j]);result=std::max(result,s);}return result;}
inline M inverse(M m) {
    M out{1,0,0,0,1,0,0,0,1};
    for(int k=0;k<3;++k) {
        int pivot=k;for(int i=k+1;i<3;++i)if(std::abs(m[3*i+k])>std::abs(m[3*pivot+k]))pivot=i;
        if(std::abs(m[3*pivot+k])<1e-30)throw std::runtime_error("singular strain gradient");
        for(int j=0;j<3;++j) {std::swap(m[3*k+j],m[3*pivot+j]);std::swap(out[3*k+j],out[3*pivot+j]);}
        const double divisor=m[3*k+k];for(int j=0;j<3;++j) {m[3*k+j]/=divisor;out[3*k+j]/=divisor;}
        for(int i=0;i<3;++i)if(i!=k) {const double v=m[3*i+k];for(int j=0;j<3;++j) {m[3*i+j]-=v*m[3*k+j];out[3*i+j]-=v*out[3*k+j];}}
    }return out;
}
struct Image {V p;unsigned target;std::array<int,3> velocity{1,1,1},coordinate{1,1,1};unsigned code=0;};
struct Edge {unsigned owner,target,code;V r,b;double weight=0;std::array<int,3> velocity,coordinate;};
class Operator {
    std::vector<Edge> edges;
    std::vector<std::vector<unsigned>> outgoing,incoming;
    std::vector<M> gradient,adjoint,edge_adjoint;
    std::vector<V> edge_force;
    std::vector<double> edge_power;
    unsigned count;
    double norm_product=0,degree=0,inbound=0;
public:
    double maximum_condition=0,maximum_linear_error=0;
    Operator(const std::vector<V> &p,V upper,std::array<bool,3> periodic,std::array<int,6> boundary,double h):count(p.size()) {
        if(count<2 || h<=0)throw std::runtime_error("invalid strain geometry");
        std::vector<Image> images;images.reserve(count*2);
        for(unsigned j=0;j<count;++j) {
            std::vector<Image> copies{{p[j],j,{1,1,1},{1,1,1},0}};
            for(int axis=0;axis<3;++axis)if(!periodic[axis]) {
                const auto originals=copies;
                for(int side=0;side<2;++side) {
                    int bc=boundary[2*axis+side];double plane=side ? upper[axis] : 0;
                    if(!bc || std::abs(p[j][axis]-plane)>=h)continue;
                    for(auto image:originals) {
                        image.p[axis]=2*plane-image.p[axis];image.coordinate[axis]*=-1;
                        if(bc==1)image.velocity[axis]*=-1;
                        else if(bc==2)for(auto &v:image.velocity)v*=-1;
                        else throw std::runtime_error("invalid solid traction");
                        image.code+=unsigned((side+1)*std::pow(3,axis));copies.push_back(image);
                    }
                }
            }
            images.insert(images.end(),copies.begin(),copies.end());
        }
        std::array<int,3> dims;V cell_width;
        for(int k=0;k<3;++k) {
            if(periodic[k]) {dims[k]=int(std::floor(upper[k]/h));if(dims[k]<3)throw std::runtime_error("periodic domain too narrow");cell_width[k]=upper[k]/dims[k];}
            else {dims[k]=int(std::ceil(upper[k]/h))+6;cell_width[k]=h;}
        }
        auto cell=[&](V point) {std::array<int,3> c;for(int k=0;k<3;++k) {if(periodic[k]) {point[k]-=std::floor(point[k]/upper[k])*upper[k];c[k]=std::min(dims[k]-1,int(point[k]/cell_width[k]));}else c[k]=int(std::floor(point[k]/h))+3;}return c;};
        auto key=[&](std::array<int,3> c) {return (std::size_t(c[0])*dims[1]+c[1])*dims[2]+c[2];};
        std::vector<std::vector<unsigned>> bins(std::size_t(dims[0])*dims[1]*dims[2]);
        for(unsigned j=0;j<images.size();++j) {auto c=cell(images[j].p);for(int k=0;k<3;++k)if(c[k]<0 || c[k]>=dims[k])throw std::runtime_error("strain search bounds exceeded");bins[key(c)].push_back(j);}
        std::vector<std::vector<Edge>> local(count);std::vector<double> conditions(count),errors(count);
        #pragma omp parallel for schedule(static)
        for(unsigned i=0;i<count;++i) {
            M moment{};auto c=cell(p[i]);
            for(int x=-1;x<=1;++x)for(int y=-1;y<=1;++y)for(int z=-1;z<=1;++z) {
                std::array<int,3> q{c[0]+x,c[1]+y,c[2]+z};bool valid=true;
                for(int k=0;k<3;++k) {if(periodic[k])q[k]=(q[k]+dims[k])%dims[k];else if(q[k]<0 || q[k]>=dims[k])valid=false;}
                if(!valid)continue;
                for(unsigned image_index:bins[key(q)]) {
                    const auto &image=images[image_index];V r=minus(image.p,p[i]);
                    for(int k=0;k<3;++k)if(periodic[k])r[k]-=std::round(r[k]/upper[k])*upper[k];
                    const double r2=dot(r,r);if(r2==0 || r2>=h*h)continue;
                    const double t=1-std::sqrt(r2)/h,w=t*t*t;
                    for(int a=0;a<3;++a)for(int b=0;b<3;++b)moment[3*a+b]+=w*r[a]*r[b];
                    local[i].push_back({i,image.target,image.code,r,{},0,image.velocity,image.coordinate});
                }
            }
            // Throwing inside an OpenMP region is avoided; invalid geometry is
            // recorded and rejected after every owner has finished construction.
            M inv{};try {inv=inverse(moment);}catch(const std::runtime_error &) {conditions[i]=1e300;continue;}
            conditions[i]=norminf(moment)*norminf(inv);
            M linear{};double total_weight=0;
            for(auto &edge:local[i]) {
                const double q=std::sqrt(dot(edge.r,edge.r))/h,t=1-q;
                edge.b=mv(inv,times(edge.r,t*t*t));edge.weight=t*t*t*t*(1+4*q);total_weight+=edge.weight;
                for(int a=0;a<3;++a)for(int b=0;b<3;++b)linear[3*a+b]+=edge.r[a]*edge.b[b];
            }
            for(auto &edge:local[i])edge.weight/=total_weight;
            for(int a=0;a<3;++a)for(int b=0;b<3;++b)errors[i]=std::max(errors[i],std::abs(linear[3*a+b]-(a==b ? 1 : 0)));
            std::sort(local[i].begin(),local[i].end(),[](const Edge &a,const Edge &b) {return a.target<b.target || (a.target==b.target && a.code<b.code);});
        }
        outgoing.resize(count);incoming.resize(count);gradient.resize(count);adjoint.resize(count);
        for(unsigned i=0;i<count;++i) {
            maximum_condition=std::max(maximum_condition,conditions[i]);maximum_linear_error=std::max(maximum_linear_error,errors[i]);
            if(conditions[i]>1e6 || errors[i]>1e-9)throw std::runtime_error("unresolved or ill-conditioned strain gradient");
            for(const auto &edge:local[i]) {unsigned e=edges.size();edges.push_back(edge);outgoing[i].push_back(e);incoming[edge.target].push_back(e);}
        }
        edge_adjoint.resize(edges.size());edge_force.resize(edges.size());edge_power.resize(edges.size());
        std::vector<double> column(count),degree_sum(count),inbound_sum(count);double row=0;
        for(unsigned i=0;i<count;++i) {
            V total{},absolute{};
            for(auto index:outgoing[i]) {const auto &e=edges[index];total=plus(total,e.b);double sum=0;for(int k=0;k<3;++k) {absolute[k]+=std::abs(e.b[k]);sum+=std::abs(e.b[k]);}column[e.target]+=sum;inbound_sum[e.target]+=e.weight;degree_sum[i]+=e.weight/dot(e.r,e.r);degree_sum[e.target]+=e.weight/dot(e.r,e.r);}
            for(int k=0;k<3;++k) {row=std::max(row,absolute[k]+std::abs(total[k]));column[i]+=std::abs(total[k]);}
        }
        norm_product=row*(*std::max_element(column.begin(),column.end()));degree=*std::max_element(degree_sum.begin(),degree_sum.end());inbound=*std::max_element(inbound_sum.begin(),inbound_sum.end());
    }
    double eigenvalue_bound(double nu) const {return 2*nu*((1+inbound)*norm_product+4*degree);}
    double apply(const std::vector<V> &velocity,double nu,std::vector<V> &acceleration) {
        if(velocity.size()!=count)throw std::runtime_error("strain velocity count differs");
        acceleration.assign(count,{});
        #pragma omp parallel for schedule(static)
        for(unsigned i=0;i<count;++i) {
            M g{};for(auto index:outgoing[i]) {const auto &e=edges[index];V delta;for(int a=0;a<3;++a)delta[a]=e.velocity[a]*velocity[e.target][a]-velocity[i][a];for(int a=0;a<3;++a)for(int b=0;b<3;++b)g[3*a+b]+=delta[a]*e.b[b];}gradient[i]=g;
        }
        #pragma omp parallel for schedule(static)
        for(unsigned index=0;index<edges.size();++index) {
            const auto &e=edges[index];M average{};V difference{};
            for(int a=0;a<3;++a) {difference[a]=e.velocity[a]*velocity[e.target][a]-velocity[e.owner][a];for(int b=0;b<3;++b)average[3*a+b]=(gradient[e.owner][3*a+b]+e.velocity[a]*e.coordinate[b]*gradient[e.target][3*a+b])*.5;}
            const double r2=dot(e.r,e.r);const V residual=minus(difference,mv(average,e.r));M g=average;
            for(int a=0;a<3;++a)for(int b=0;b<3;++b)g[3*a+b]+=residual[a]*e.r[b]/r2;
            M stress{};double power=0;
            for(int a=0;a<3;++a)for(int b=0;b<3;++b) {double d=(g[3*a+b]+g[3*b+a])*.5;stress[3*a+b]=2*nu*e.weight*d;power+=2*nu*e.weight*d*d;}
            V force=times(mv(stress,e.r),1/r2);M dual=stress;
            for(int a=0;a<3;++a)for(int b=0;b<3;++b)dual[3*a+b]-=force[a]*e.r[b];
            edge_force[index]=force;edge_adjoint[index]=dual;edge_power[index]=power;
        }
        #pragma omp parallel for schedule(static)
        for(unsigned i=0;i<count;++i) {
            M dual{};V a{};
            for(auto index:outgoing[i]) {a=plus(a,edge_force[index]);for(int k=0;k<9;++k)dual[k]+=.5*edge_adjoint[index][k];}
            for(auto index:incoming[i]) {const auto &e=edges[index];for(int k=0;k<3;++k)a[k]-=e.velocity[k]*edge_force[index][k];for(int k=0;k<3;++k)for(int l=0;l<3;++l)dual[3*k+l]+=.5*e.velocity[k]*e.coordinate[l]*edge_adjoint[index][3*k+l];}
            adjoint[i]=dual;acceleration[i]=a;
        }
        #pragma omp parallel for schedule(static)
        for(unsigned i=0;i<count;++i) {
            V a=acceleration[i];for(auto index:outgoing[i])a=plus(a,mv(adjoint[i],edges[index].b));
            for(auto index:incoming[i]) {const auto &e=edges[index];V contribution=mv(adjoint[e.owner],e.b);for(int k=0;k<3;++k)a[k]-=e.velocity[k]*contribution[k];}
            acceleration[i]=a;
        }
        double power=0;for(double value:edge_power)power+=value;return power/count;
    }
    unsigned edge_count() const {return edges.size();}
};
}
