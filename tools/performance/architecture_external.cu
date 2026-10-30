// Headless adapter for the pinned barnden/pbf CUDA constraint/correction kernels.
// Upstream sources are supplied separately. No OpenGL resource is constructed.
#include <cuda_runtime.h>
#include <thrust/device_vector.h>
#include <thrust/scan.h>
#include <thrust/execution_policy.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include "CUDA/Kernels/Simulation/Integration.cuh"
#include "CUDA/Kernels/Simulation/FindNeighbours.cuh"
#include "CUDA/Kernels/Simulation/Quantize.cuh"
#include "CUDA/Kernels/Simulation/Solver/Constraint.cuh"
#include "CUDA/Kernels/Simulation/Solver/TensileInstability.cuh"
#include "CUDA/Kernels/Sort/Placement.cuh"
#include "solver.h"

static void checked(cudaError_t c) {if(c!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(c));}
template<class T> static T *allocate(std::size_t n) {T *p=nullptr;checked(cudaMalloc(&p,n*sizeof(T)));return p;}
__global__ void project(pbf::Particles::DevicePointers p,float3 upper,float scale) {
    const auto i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=p.size)return;
    auto x=p.d_position_star[i]+p.d_position_delta[i]*scale;
    p.d_position_star[i]={fmaxf(0,fminf(x.x,upper.x)),fmaxf(0,fminf(x.y,upper.y)),fmaxf(0,fminf(x.z,upper.z))};
}
__global__ void velocity(pbf::Particles::DevicePointers p,float timestep) {
    const auto i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=p.size)return;
    p.d_velocity[i]=(p.d_position_star[i]-p.d_position[i])/timestep;
    p.d_position[i]=p.d_position_star[i];
}
int main(int argc,char **argv) try {
    if(argc!=7)throw std::runtime_error("input steps iterations prefix observations aligned");
    const unsigned steps=std::stoul(argv[2]),iterations=std::stoul(argv[3]);const std::string prefix=argv[4];
    const bool observations=std::stoul(argv[5]),aligned=std::stoul(argv[6]);
    SolverSettings s{};std::ifstream input(argv[1],std::ios::binary);input.read(reinterpret_cast<char *>(&s),sizeof(s));
    if(!input || !s.count || s.count>512000 || !steps || steps>10000 || !iterations || iterations>64)
        throw std::runtime_error("invalid external request");
    std::vector<float3> initial(s.count),v(s.count);std::vector<DevicePlane> planes(s.planes);
    input.read(reinterpret_cast<char *>(initial.data()),s.count*sizeof(float3));input.read(reinterpret_cast<char *>(v.data()),s.count*sizeof(float3));
    input.read(reinterpret_cast<char *>(planes.data()),s.planes*sizeof(DevicePlane));
    if(!input || input.peek()!=EOF || s.planes!=6)throw std::runtime_error("external input differs");
    const float3 upper={-planes[1].offset,-planes[3].offset,-planes[5].offset};
    pbf::Particles::DevicePointers p{};p.size=s.count;
    p.d_position=allocate<float3>(s.count);p.d_position_star=allocate<float3>(s.count);
    p.d_position_delta=allocate<float3>(s.count);p.d_velocity=allocate<float3>(s.count);
    p.d_density=allocate<float>(s.count);p.d_constraint=allocate<float>(s.count);p.d_vorticity=allocate<float3>(s.count);
    checked(cudaMemcpy(p.d_position,initial.data(),s.count*sizeof(float3),cudaMemcpyHostToDevice));
    checked(cudaMemcpy(p.d_velocity,v.data(),s.count*sizeof(float3),cudaMemcpyHostToDevice));
    constexpr unsigned cells=262147,cap=512;
    // The extra sentinel repairs upstream's last-cell end lookup. Placement
    // decrements inclusive totals into starts; the sentinel remains count.
    thrust::device_vector<unsigned> grid(cells+1),indices(s.count);
    auto *rows=allocate<unsigned>(static_cast<std::size_t>(s.count)*cap);
    auto *g=thrust::raw_pointer_cast(grid.data());auto *sorted=thrust::raw_pointer_cast(indices.data());
    const unsigned blocks=(s.count+127)/128;
    auto save=[&](unsigned step) {
        std::vector<float3> x(s.count),y(s.count);checked(cudaMemcpy(x.data(),p.d_position,s.count*sizeof(float3),cudaMemcpyDeviceToHost));
        checked(cudaMemcpy(y.data(),p.d_velocity,s.count*sizeof(float3),cudaMemcpyDeviceToHost));
        std::ofstream file(prefix+"-"+std::to_string(step)+".bin",std::ios::binary);
        file.write(reinterpret_cast<const char *>(x.data()),s.count*sizeof(float3));file.write(reinterpret_cast<const char *>(y.data()),s.count*sizeof(float3));
        if(!file)throw std::runtime_error("external snapshot write failed");
        if(step) {
            std::vector<unsigned> host(static_cast<std::size_t>(s.count)*cap);
            checked(cudaMemcpy(host.data(),rows,host.size()*4,cudaMemcpyDeviceToHost));
            unsigned capped=0,duplicate=0;std::uint64_t total=0;std::vector<unsigned> counts;
            for(unsigned i=0;i<s.count;++i) {
                const auto start=host.begin()+static_cast<std::size_t>(i)*cap;const unsigned count=*start;
                if(count>=cap-1)++capped;if(count>cap-1)throw std::runtime_error("external row overflow");
                total+=count;counts.push_back(count);
                std::vector<unsigned> row(start+1,start+1+count);std::sort(row.begin(),row.end());
                if(std::adjacent_find(row.begin(),row.end())!=row.end())++duplicate;
            }
            std::sort(counts.begin(),counts.end());
            std::ofstream audit(prefix+"-"+std::to_string(step)+"-rows.json");
            audit<<"{\"capped\":"<<capped<<",\"duplicate_rows\":"<<duplicate<<",\"entries\":"<<total
                <<",\"min\":"<<counts.front()<<",\"median\":"<<counts[counts.size()/2]<<",\"p95\":"<<counts[counts.size()*95/100]<<",\"max\":"<<counts.back()<<"}\n";
        }
    };
    if(observations)save(0);
    double total=0;
    pbf::parameters::physical::ArtificialPressure pressure;
    pressure.deltaQ=.2f;pressure.n=4;pressure.k=s.strength;
    for(unsigned step=1;step<=steps;++step) {
        const auto start=std::chrono::steady_clock::now();
        pbf::kernels::simulation::euler_integration<<<blocks,128>>>(p,{s.acceleration.x,s.acceleration.y,s.acceleration.z},s.timestep);
        checked(cudaMemset(g,0,cells*sizeof(unsigned)));
        checked(cudaMemcpy(g+cells,&s.count,4,cudaMemcpyHostToDevice));
        // Matched prediction-time membership is an explicit adapter change.
        auto *positions=aligned?p.d_position_star:p.d_position;
        pbf::kernels::simulation::quantize<<<blocks,128>>>(positions,g,cells,s.count,s.radius);
        thrust::inclusive_scan(thrust::device,grid.begin(),grid.begin()+cells,grid.begin());
        auto keyof=[radius=s.radius] __device__(float3 x) -> unsigned {return pbf::spatial::hash(x,radius,cells);};
        pbf::kernels::sort::placement<<<((s.count+255)/256+127)/128,128>>>(keyof,positions,g,sorted,s.count,256);
        auto search=p;search.d_position=positions;
        pbf::kernels::simulation::find_neighbours<<<blocks,128>>>(search,g,sorted,rows,s.radius,s.radius,cells,cap);
        for(unsigned k=0;k<iterations;++k) {
            pbf::kernels::solver::compute_constraints<<<blocks,128>>>(p,rows,s.rest_density,s.relaxation,s.radius,cap);
            pbf::kernels::solver::compute_tensile_instability<<<blocks,128>>>(p,rows,s.rest_density,s.radius,pressure,cap);
            project<<<blocks,128>>>(p,upper,s.correction_scale);
        }
        velocity<<<blocks,128>>>(p,s.timestep);
        checked(cudaGetLastError());checked(cudaDeviceSynchronize());
        total+=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        if(observations && (step==1 || step==120 || step==240 || step==480))save(step);
    }
    save(steps);
    std::cout.precision(17);std::cout<<"{\"solver_s\":"<<total<<",\"steps\":"<<steps<<",\"particles\":"<<s.count<<"}\n";
    return 0;
} catch(const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
