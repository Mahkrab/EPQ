// Experimental execution driver for frozen Maelstrom device code. This has no
// production acceptance API: deferred observations deliberately change that API.
#include <cuda_runtime.h>
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include "kernels.cu"

static void checked(cudaError_t code) {
    if (code != cudaSuccess) throw std::runtime_error(cudaGetErrorString(code));
}
template<class T> static T *allocate(std::size_t n) {
    T *p=nullptr; checked(cudaMalloc(&p,n*sizeof(T))); return p;
}
static auto now() { return std::chrono::steady_clock::now(); }
static double seconds(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration<double>(now()-start).count();
}
static std::vector<Vector> transfer_layout(std::vector<Vector> v, bool to_device) {
#ifdef ARCH_SOA
    std::vector<Vector> output(v.size());
    float *dst=reinterpret_cast<float *>(output.data());
    const float *src=reinterpret_cast<const float *>(v.data());
    for (std::size_t i=0;i<v.size();++i) for (unsigned axis=0;axis<3;++axis)
        if (to_device) dst[axis*v.size()+i]=src[3*i+axis];
        else dst[3*i+axis]=src[axis*v.size()+i];
    return output;
#else
    (void)to_device;return v;
#endif
}
struct HostParticle { std::uint64_t identity; Vector position,velocity; };

int main(int argc,char **argv) try {
    if (argc!=9) throw std::runtime_error("input steps iterations mode output-prefix observations effects");
    const unsigned steps=std::stoul(argv[2]), iterations=std::stoul(argv[3]);
    const std::string mode=argv[4], prefix=argv[5];
    const bool observations=std::stoul(argv[6]), effects=std::stoul(argv[7]);
    const unsigned cadence=std::stoul(argv[8]);
    if (mode!="checked" && mode!="deferred" && mode!="snapshots" && mode!="resident")
        throw std::runtime_error("unknown execution experiment");
    const bool group_waits=mode!="deferred" && mode!="resident";
    const bool snapshots=mode!="snapshots" && mode!="resident";
    const bool summaries=mode!="resident";
    SolverSettings s{};
    std::ifstream input(argv[1],std::ios::binary);input.read(reinterpret_cast<char *>(&s),sizeof(s));
    if (!input || !s.count || s.count>512000 || s.planes>32 || !iterations || iterations>64 || !steps || steps>10000)
        throw std::runtime_error("invalid bounded experiment input");
    std::vector<Vector> initial(s.count), zero(s.count);
    std::vector<DevicePlane> planes(s.planes);
    input.read(reinterpret_cast<char *>(initial.data()),initial.size()*sizeof(Vector));
    input.read(reinterpret_cast<char *>(zero.data()),zero.size()*sizeof(Vector));
    input.read(reinterpret_cast<char *>(planes.data()),planes.size()*sizeof(DevicePlane));
    if (!input || input.peek()!=EOF) throw std::runtime_error("input size differs");
    checked(cudaSetDevice(0));
#ifdef ARCH_SOA
    checked(cudaMemcpyToSymbol(arch_count,&s.count,sizeof(s.count)));
#endif
    SolverBuffers b{};
    b.old_position=allocate<Vector>(s.count);b.position=allocate<Vector>(s.count);
    b.old_velocity=allocate<Vector>(s.count+2);b.velocity=allocate<Vector>(s.count+2);
    b.density=allocate<float>(s.count);b.constraint=allocate<float>(s.count);b.multiplier=allocate<float>(s.count);
    b.correction=allocate<Vector>(s.count+32);b.candidate=reinterpret_cast<Vector *>(allocate<PendingJacobi>(s.count));
    b.planes=allocate<DevicePlane>(s.planes);b.cells=allocate<Cell>(2*s.padded);
    // Conservative private capacity permits the resident experiment to avoid a
    // host allocation decision. A separate count audit rejects overflow.
    const std::uint64_t capacity=static_cast<std::uint64_t>(s.count)*512;
    b.neighbours=allocate<std::uint32_t>(capacity);b.errors=allocate<std::uint32_t>(s.count);
    b.offsets=allocate<std::uint64_t>(s.count+1);b.diagnostic=allocate<unsigned long long>(5);
    unsigned long long *mirror=nullptr;checked(cudaHostAlloc(&mirror,32,cudaHostAllocMapped));
    std::fill_n(mirror,4,ULLONG_MAX);unsigned long long *mapped=nullptr;
    checked(cudaHostGetDevicePointer(&mapped,mirror,0));
    checked(cudaMemset(b.diagnostic,0xff,32));
    checked(cudaMemcpy(b.diagnostic+4,&mapped,sizeof(mapped),cudaMemcpyHostToDevice));
    auto packed=transfer_layout(initial,true);
    checked(cudaMemcpy(b.old_position,packed.data(),s.count*sizeof(Vector),cudaMemcpyHostToDevice));
    checked(cudaMemcpy(b.old_velocity,zero.data(),s.count*sizeof(Vector),cudaMemcpyHostToDevice));
    checked(cudaMemcpy(b.planes,planes.data(),s.planes*sizeof(DevicePlane),cudaMemcpyHostToDevice));
    const unsigned blocks=(s.count+127)/128;
    std::vector<StateSummary> summary(blocks);
    std::vector<Vector> host_position(s.count),host_velocity(s.count+2);
    std::vector<HostParticle> host(s.count);
    for (unsigned i=0;i<s.count;++i) host[i]={i,initial[i],zero[i]};
    std::uint64_t launches=0,waits=0,copies=0,copy_bytes=0;
    auto sync=[&]() {checked(cudaDeviceSynchronize());++waits;};
    auto check_packet=[&]() {for (unsigned i=0;i<4;++i) if (mirror[i]!=ULLONG_MAX) throw std::runtime_error("device numerical diagnostic");};
    auto download=[&](void *dst,const void *src,std::size_t bytes) {
        checked(cudaMemcpy(dst,src,bytes,cudaMemcpyDeviceToHost));++copies;copy_bytes+=bytes;
    };
    auto launch=[&](unsigned op,std::uint64_t count=0) {
        solver<<<((count?count:s.count)+127)/128,128>>>(b,s,op);++launches;
    };
    auto packet=[&]() {if (group_waits) {sync();check_packet();}};
    auto save=[&](unsigned step,Vector *position,Vector *velocity) {
        std::vector<Vector> p(s.count),v(s.count);
        checked(cudaMemcpy(p.data(),position,s.count*sizeof(Vector),cudaMemcpyDeviceToHost));
        checked(cudaMemcpy(v.data(),velocity,s.count*sizeof(Vector),cudaMemcpyDeviceToHost));
        p=transfer_layout(std::move(p),false);
        std::ofstream file(prefix+"-"+std::to_string(step)+".bin",std::ios::binary);
        file.write(reinterpret_cast<const char *>(p.data()),p.size()*sizeof(Vector));
        file.write(reinterpret_cast<const char *>(v.data()),v.size()*sizeof(Vector));
        if (!file) throw std::runtime_error("snapshot write failed");
    };
    if (observations) save(0,b.old_position,b.old_velocity);
    std::vector<double> durations;
    for (unsigned step=1;step<=steps;++step) {
        const auto start=now();
        if (snapshots) for (const auto &p:host)
            if (!std::isfinite(p.position.x) || !std::isfinite(p.position.y) || !std::isfinite(p.position.z) ||
                !std::isfinite(p.velocity.x) || !std::isfinite(p.velocity.y) || !std::isfinite(p.velocity.z))
                throw std::runtime_error("host input nonfinite");
        b.first_operation=0;
        observe_state<<<blocks,128>>>(b,s,0);++launches;packet();
        if (summaries) download(summary.data(),b.correction,blocks*sizeof(StateSummary));
        observe_state<<<blocks,128>>>(b,s,1);++launches;packet();
        if (summaries) {
            download(summary.data(),b.correction,blocks*sizeof(StateSummary));
            double largest=0;
            for (const auto &value:summary) largest=std::max(largest,static_cast<double>(value.scalar));
            const double minimum=std::max(static_cast<double>(s.radius),std::max(std::ldexp(1.0,-72),std::ldexp(largest,-50)));
            s.width=std::ldexp(1.0,-72);while (s.width<minimum) s.width*=2;
        } else s.width=0.125;
        launch(2,s.padded);
        unsigned merges=0;for (std::uint64_t width=128;width<s.padded;width*=2) ++merges;
        s.stride=merges&1;s.span=0;
        spatial_sort<<<(s.padded+127)/128,128>>>(b,s,19);++launches;
        for (std::uint64_t width=128;width<s.padded;width*=2) {
            s.span=width;spatial_sort<<<(s.padded+127)/128,128>>>(b,s,20);++launches;s.stride^=1;
        }
        launch(4);
        s.stride=1;s.span=(static_cast<std::uint64_t>(s.count)+128)/128;
        for (unsigned op=21;op<=23;++op) {
            prefix_counts<<<(op==22?1:(s.count+128)/128),128>>>(b,s,op);++launches;
        }
        packet();
        if (mode!="resident") {
            download(&s.entries,b.offsets+s.count,8);
            if (s.entries>capacity) throw std::runtime_error("neighbour capacity exceeded");
        } else s.entries=capacity;
        launch(12);launch(18,static_cast<std::uint64_t>(s.count)*32);packet();
        for (unsigned iteration=0;iteration<iterations;++iteration) {
            b.first_operation=5;for (unsigned op=5;op<=8;++op) launch(op);packet();
            b.first_operation=9;launch(9);launch(10);packet();
        }
        b.first_operation=0;launch(24);packet();
        if (effects) for (unsigned op:{16,17,15,14,15}) {launch(op);packet();}
        if (snapshots) {
            download(host_position.data(),b.position,s.count*sizeof(Vector));
            download(host_velocity.data(),b.velocity,s.count*sizeof(Vector)+16);
            host_position=transfer_layout(std::move(host_position),false);
            for (unsigned i=0;i<s.count;++i) {
                host[i]={i,host_position[i],host_velocity[i]};
                const auto p=host[i];
                if (!std::isfinite(p.position.x) || !std::isfinite(p.position.y) || !std::isfinite(p.position.z) ||
                    !std::isfinite(p.velocity.x) || !std::isfinite(p.velocity.y) || !std::isfinite(p.velocity.z))
                    throw std::runtime_error("host output nonfinite");
            }
        }
        // A deferred variant reports completed-step time, not enqueue time.
        // Its single completion still includes all dependencies for this step.
        if (!group_waits) {sync();check_packet();}
        std::swap(b.old_position,b.position);std::swap(b.old_velocity,b.velocity);
        durations.push_back(seconds(start));
        if (observations && (step==1 || (cadence && step%cadence==0) || step==steps))
            save(step,b.old_position,b.old_velocity);
    }
    checked(cudaGetLastError());checked(cudaDeviceSynchronize());check_packet();
    std::uint64_t actual=0;checked(cudaMemcpy(&actual,b.offsets+s.count,8,cudaMemcpyDeviceToHost));
    if (actual>capacity) throw std::runtime_error("resident capacity audit failed");
    save(steps,b.old_position,b.old_velocity);
    std::vector<std::uint64_t> offsets(s.count+1);
    checked(cudaMemcpy(offsets.data(),b.offsets,offsets.size()*8,cudaMemcpyDeviceToHost));
    std::ofstream rows(prefix+"-rows.bin",std::ios::binary);
    rows.write(reinterpret_cast<const char *>(offsets.data()),offsets.size()*8);
    double total=0;for (double value:durations) total+=value;
    std::cout.precision(17);
    std::cout<<"{\"solver_s\":"<<total<<",\"steps\":"<<steps<<",\"particles\":"<<s.count
             <<",\"launches\":"<<launches<<",\"explicit_waits\":"<<waits<<",\"dtoh_copies\":"<<copies
             <<",\"dtoh_bytes\":"<<copy_bytes<<",\"last_neighbour_entries\":"<<actual<<",\"step_s\":[";
    for (unsigned i=0;i<durations.size();++i) std::cout<<(i?",":"")<<durations[i];
    std::cout<<"]}\n";
    // Process exit releases this private runtime context and every allocation.
    return 0;
} catch (const std::exception &e) {std::cerr<<e.what()<<"\n";return 1;}
