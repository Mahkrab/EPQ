// Query resources from the driver-loaded PTX, independently of timed solver work.
// The bridge owns this probe's isolated context and releases it on every exit.
#include "bridge.cpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

int main(int argc, char **argv) {
    if (argc!=2) return 2;
    std::ifstream file(argv[1],std::ios::binary);
    if (!file) return 2;
    const std::string ptx((std::istreambuf_iterator<char>(file)),std::istreambuf_iterator<char>());
    Resource resource;
    auto status=resource.driver.load();
    DeviceInfo info{};
    if (!status.code) status=initialise(resource,0,ptx.c_str(),89,&info);
    if (status.code) { std::cerr<<"module load failed: "<<status.code<<'\n';return 1; }
    auto attribute=reinterpret_cast<decltype(&cuFuncGetAttribute)>(dlsym(resource.driver.library,"cuFuncGetAttribute"));
    if (!attribute) return 1;
    if (resource.driver.cuCtxPushCurrent_fn(resource.context)!=CUDA_SUCCESS) return 1;
    std::cout<<"{\"scope\":\"driver-loaded function resources, not achieved occupancy\",\"functions\":[";
#ifdef SPECIALISED
    const auto count=solver_operation_count;
#else
    const auto count=1U;
#endif
    bool failed=false;
    for (unsigned int i=0;i<count && !failed;++i) {
#ifdef SPECIALISED
        const auto function=resource.solvers[i];
        const auto name=solver_names[i];
#else
        const auto function=resource.solver;
        const auto name="solver";
#endif
        int values[6]{};
        const CUfunction_attribute fields[]={CU_FUNC_ATTRIBUTE_NUM_REGS,CU_FUNC_ATTRIBUTE_LOCAL_SIZE_BYTES,
            CU_FUNC_ATTRIBUTE_SHARED_SIZE_BYTES,CU_FUNC_ATTRIBUTE_MAX_THREADS_PER_BLOCK,
            CU_FUNC_ATTRIBUTE_BINARY_VERSION,CU_FUNC_ATTRIBUTE_PTX_VERSION};
        for (unsigned int j=0;j<6;++j)
            if (attribute(&values[j],fields[j],function)!=CUDA_SUCCESS) { failed=true;break; }
        if (failed) break;
        if (i) std::cout<<',';
        std::cout<<"{\"name\":\""<<name<<"\",\"registers\":"<<values[0]
            <<",\"local_bytes\":"<<values[1]<<",\"shared_bytes\":"<<values[2]
            <<",\"max_threads\":"<<values[3]<<",\"binary_version\":"<<values[4]
            <<",\"ptx_version\":"<<values[5]<<'}';
    }
    std::cout<<"]}\n";
    CUcontext previous;
    if (resource.driver.cuCtxPopCurrent_fn(&previous)!=CUDA_SUCCESS) failed=true;
    return failed ? 1 : 0;
}
