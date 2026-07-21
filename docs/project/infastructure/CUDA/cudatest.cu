#include <cuda_runtime.h>

#include <cstdio>

__global__ void add_one(int *value) {
    *value += 1;
}

int main() {
    int device_count = 0;
    cudaError_t error = cudaGetDeviceCount(&device_count);

    if (error != cudaSuccess || device_count == 0) {
        std::fprintf(stderr, "CUDA device check failed: %s\n",
                     cudaGetErrorString(error));
        return 1;
    }

    int host_value = 41;
    int *device_value = nullptr;

    if (cudaMalloc(&device_value, sizeof(host_value)) != cudaSuccess ||
        cudaMemcpy(device_value, &host_value, sizeof(host_value),
                   cudaMemcpyHostToDevice) != cudaSuccess) {
        std::fprintf(stderr, "CUDA memory setup failed\n");
        cudaFree(device_value);
        return 1;
    }

    add_one<<<1, 1>>>(device_value);
    error = cudaDeviceSynchronize();

    if (error != cudaSuccess ||
        cudaMemcpy(&host_value, device_value, sizeof(host_value),
                   cudaMemcpyDeviceToHost) != cudaSuccess) {
        std::fprintf(stderr, "CUDA kernel failed: %s\n",
                     cudaGetErrorString(error));
        cudaFree(device_value);
        return 1;
    }

    cudaFree(device_value);
    std::printf("CUDA works: 41 + 1 = %d (%d device found)\n", host_value,
                device_count);

    return host_value == 42 ? 0 : 1;
}
