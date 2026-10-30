// Isolated fixed-domain MAC pressure cost experiment. The spectral factorisation
// is specific to periodic horizontal directions, a flat bed and a flat surface.
// Neither solver includes advection, particle transfer or changing fluid geometry.
#include <cuda_runtime.h>
#include <cufft.h>
#include <cublas_v2.h>
#include <cmath>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#define CU(x) do {auto e=(x);if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}while(0)
#define BL(x) do {if((x)!=CUBLAS_STATUS_SUCCESS)throw std::runtime_error("cuBLAS error");}while(0)
#define FT(x) do {if((x)!=CUFFT_SUCCESS)throw std::runtime_error("cuFFT error");}while(0)
constexpr int block=128;
constexpr double pi=3.14159265358979323846;
struct Grid {int nx,ny,nz,n,plane;double hx,hy,hz,lx,H,lz;};

__device__ void location(int i,Grid g,int &x,int &y,int &z){y=i/g.plane;z=(i%g.plane)/g.nx;x=i%g.nx;}
__device__ int ix(int x,int y,int z,Grid g){return (x+g.nx)%g.nx+g.nx*((z+g.nz)%g.nz+g.nz*y);}
__device__ double grad(const double *p,int i,int axis,Grid g){
    int x,y,z;location(i,g,x,y,z);
    if(axis==0)return (p[ix(x+1,y,z,g)]-p[i])/g.hx;
    if(axis==2)return (p[ix(x,y,z+1,g)]-p[i])/g.hz;
    return y==g.ny-1?-2*p[i]/g.hy:(p[i+g.plane]-p[i])/g.hy;
}
__global__ void initialise(double *vx,double *vy,double *vz,double *truth,Grid g){
    int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=g.n)return;int x,y,z;location(i,g,x,y,z);
    double px=(x+.5)/g.nx,py=(y+.5)/g.ny,pz=(z+.5)/g.nz;
    vx[i]=.5*sin(2*pi*pz);vy[i]=vz[i]=0;
    double p=1000*9.81*g.H*(1-py);
    // Several resolved modes plus the hydrostatic ramp avoid timing only the
    // exceptional one-eigenmode case of a Krylov solve.
    for(int k=1;k<=8;k++)p+=20./(k*k)*cos(2*pi*k*px)*sin(2*pi*(k%3+1)*pz)*cos(pi*(k%4+.5)*py);
    truth[i]=p;
}
__global__ void kick(double *vx,double *vy,double *vz,const double *p,double dt,Grid g){
    int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=g.n)return;
    vx[i]+=dt/1000*grad(p,i,0,g);vy[i]+=dt/1000*grad(p,i,1,g);vz[i]+=dt/1000*grad(p,i,2,g);
}
__global__ void rhs_kernel(const double *vx,const double *vy,const double *vz,double *b,double dt,Grid g){
    int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=g.n)return;int x,y,z;location(i,g,x,y,z);
    double div=(vx[i]-vx[ix(x-1,y,z,g)])/g.hx+(vz[i]-vz[ix(x,y,z-1,g)])/g.hz;
    div+=(vy[i]-(y==0?0:vy[i-g.plane]))/g.hy;b[i]=-1000/dt*div;
}
__global__ void project(double *vx,double *vy,double *vz,const double *p,double dt,Grid g){
    int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=g.n)return;
    vx[i]-=dt/1000*grad(p,i,0,g);vy[i]-=dt/1000*grad(p,i,1,g);vz[i]-=dt/1000*grad(p,i,2,g);
}
__global__ void apply(const double *p,double *Ap,Grid g){
    int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=g.n)return;int x,y,z;location(i,g,x,y,z);
    double a=(2*p[i]-p[ix(x-1,y,z,g)]-p[ix(x+1,y,z,g)])/(g.hx*g.hx);
    a+=(2*p[i]-p[ix(x,y,z-1,g)]-p[ix(x,y,z+1,g)])/(g.hz*g.hz);
    a+=(y==0?p[i]-p[i+g.plane]:(y==g.ny-1?3*p[i]-p[i-g.plane]:2*p[i]-p[i-g.plane]-p[i+g.plane]))/(g.hy*g.hy);
    Ap[i]=a;
}
__global__ void precondition(const double *r,double *z,Grid g){
    int i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=g.n)return;int y=i/g.plane;
    double diag=2/(g.hx*g.hx)+2/(g.hz*g.hz)+(y==0?1:(y==g.ny-1?3:2))/(g.hy*g.hy);z[i]=r[i]/diag;
}
__global__ void to_complex(const double *b,cufftDoubleComplex *q,int n){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<n)q[i]={b[i],0};}
__global__ void to_real(const cufftDoubleComplex *q,double *p,Grid g){int i=blockIdx.x*blockDim.x+threadIdx.x;if(i<g.n)p[i]=q[i].x/g.plane;}
__global__ void factors(double *inv,double *cp,Grid g){
    int k=blockIdx.x*blockDim.x+threadIdx.x;if(k>=g.plane)return;int x=k%g.nx,z=k/g.nx;
    double alpha=4*pow(sin(pi*x/g.nx),2)/(g.hx*g.hx)+4*pow(sin(pi*z/g.nz),2)/(g.hz*g.hz),off=-1/(g.hy*g.hy),previous=0;
    for(int y=0;y<g.ny;y++){
        int i=k+y*g.plane;double diag=alpha+(y==0?1:(y==g.ny-1?3:2))/(g.hy*g.hy);
        inv[i]=1/(diag-off*previous);cp[i]=previous=off*inv[i];
    }
}
__global__ void vertical(cufftDoubleComplex *q,const double *inv,const double *cp,Grid g){
    int k=blockIdx.x*blockDim.x+threadIdx.x;if(k>=g.plane)return;double off=-1/(g.hy*g.hy);cufftDoubleComplex previous{0,0};
    for(int y=0;y<g.ny;y++){int i=k+y*g.plane;q[i]={(q[i].x-off*previous.x)*inv[i],(q[i].y-off*previous.y)*inv[i]};previous=q[i];}
    for(int y=g.ny-2;y>=0;y--){int i=k+y*g.plane;q[i].x-=cp[i]*q[i+g.plane].x;q[i].y-=cp[i]*q[i+g.plane].y;}
}
struct Device {
    double *vx,*vy,*vz,*truth,*b,*p,*r,*z,*d,*Ad,*inv,*cp;cufftDoubleComplex *q;
    explicit Device(int n){for(auto v:{&vx,&vy,&vz,&truth,&b,&p,&r,&z,&d,&Ad,&inv,&cp})CU(cudaMalloc(v,n*sizeof(double)));CU(cudaMalloc(&q,n*sizeof(cufftDoubleComplex)));}
    ~Device(){for(auto v:{vx,vy,vz,truth,b,p,r,z,d,Ad,inv,cp})cudaFree(v);cudaFree(q);}
};
int pcg(Device &a,Grid g,cublasHandle_t handle){
    size_t bytes=g.n*sizeof(double);CU(cudaMemset(a.p,0,bytes));CU(cudaMemcpy(a.r,a.b,bytes,cudaMemcpyDeviceToDevice));
    precondition<<<(g.n+block-1)/block,block>>>(a.r,a.z,g);CU(cudaMemcpy(a.d,a.z,bytes,cudaMemcpyDeviceToDevice));
    double rz,base;BL(cublasDdot(handle,g.n,a.r,1,a.z,1,&rz));BL(cublasDnrm2(handle,g.n,a.b,1,&base));if(base<1e-30)return 0;
    for(int it=1;it<=2000;it++){
        apply<<<(g.n+block-1)/block,block>>>(a.d,a.Ad,g);double dAd;BL(cublasDdot(handle,g.n,a.d,1,a.Ad,1,&dAd));
        if(!(dAd>0))throw std::runtime_error("nonpositive CG curvature");double alpha=rz/dAd,negative=-alpha;
        BL(cublasDaxpy(handle,g.n,&alpha,a.d,1,a.p,1));BL(cublasDaxpy(handle,g.n,&negative,a.Ad,1,a.r,1));
        double norm;BL(cublasDnrm2(handle,g.n,a.r,1,&norm));if(norm<=1e-10*base)return it;
        precondition<<<(g.n+block-1)/block,block>>>(a.r,a.z,g);double next;BL(cublasDdot(handle,g.n,a.r,1,a.z,1,&next));
        double beta=next/rz,one=1;BL(cublasDscal(handle,g.n,&beta,a.d,1));BL(cublasDaxpy(handle,g.n,&one,a.z,1,a.d,1));rz=next;
    }
    throw std::runtime_error("PCG iteration limit");
}
void dump(const std::string &path,const double *a,int n){std::vector<double> host(n);CU(cudaMemcpy(host.data(),a,n*sizeof(double),cudaMemcpyDeviceToHost));std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<const char*>(host.data()),n*sizeof(double));if(!out)throw std::runtime_error("field write failed");}

int main(int argc,char **argv){try{
    if(argc!=12)throw std::runtime_error("usage: solver nx ny nz lx H lz dt steps output-prefix trial");
    std::string method=argv[1],prefix=argv[10];if(method!="fft"&&method!="pcg")throw std::runtime_error("unknown solver");
    Grid g{};g.nx=std::stoi(argv[2]);g.ny=std::stoi(argv[3]);g.nz=std::stoi(argv[4]);g.lx=std::stod(argv[5]);g.H=std::stod(argv[6]);g.lz=std::stod(argv[7]);double dt=std::stod(argv[8]);int steps=std::stoi(argv[9]);
    if(g.nx<4||g.ny<2||g.nz<4||g.lx<=0||g.H<=0||g.lz<=0||dt<=0||steps<1)throw std::runtime_error("invalid domain or horizon");
    long long count=1LL*g.nx*g.ny*g.nz;if(count>2000000)throw std::runtime_error("bounded study cell limit");g.n=int(count);g.plane=g.nx*g.nz;g.hx=g.lx/g.nx;g.hy=g.H/g.ny;g.hz=g.lz/g.nz;
    auto setup_start=std::chrono::steady_clock::now();CU(cudaFree(nullptr));Device a(g.n);int blocks=(g.n+block-1)/block;cublasHandle_t handle;BL(cublasCreate(&handle));cufftHandle plan=0;
    if(method=="fft"){int dims[]={g.nz,g.nx};FT(cufftPlanMany(&plan,2,dims,nullptr,1,g.plane,nullptr,1,g.plane,CUFFT_Z2Z,g.ny));factors<<<(g.plane+block-1)/block,block>>>(a.inv,a.cp,g);}
    CU(cudaDeviceSynchronize());double setup=std::chrono::duration<double>(std::chrono::steady_clock::now()-setup_start).count();
    auto step=[&](){
        kick<<<blocks,block>>>(a.vx,a.vy,a.vz,a.truth,dt,g);rhs_kernel<<<blocks,block>>>(a.vx,a.vy,a.vz,a.b,dt,g);int iterations=0;
        if(method=="fft"){
            to_complex<<<blocks,block>>>(a.b,a.q,g.n);FT(cufftExecZ2Z(plan,a.q,a.q,CUFFT_FORWARD));vertical<<<(g.plane+block-1)/block,block>>>(a.q,a.inv,a.cp,g);FT(cufftExecZ2Z(plan,a.q,a.q,CUFFT_INVERSE));to_real<<<blocks,block>>>(a.q,a.p,g);
        }else iterations=pcg(a,g,handle);
        project<<<blocks,block>>>(a.vx,a.vy,a.vz,a.p,dt,g);CU(cudaGetLastError());return iterations;
    };
    initialise<<<blocks,block>>>(a.vx,a.vy,a.vz,a.truth,g);for(int k=0;k<3;k++)step();CU(cudaDeviceSynchronize());
    initialise<<<blocks,block>>>(a.vx,a.vy,a.vz,a.truth,g);CU(cudaDeviceSynchronize());
    cudaEvent_t start,stop;CU(cudaEventCreate(&start));CU(cudaEventCreate(&stop));std::vector<int> iterations;iterations.reserve(steps);
    auto clock_start=std::chrono::steady_clock::now();CU(cudaEventRecord(start));for(int k=0;k<steps;k++)iterations.push_back(step());CU(cudaEventRecord(stop));CU(cudaEventSynchronize(stop));double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-clock_start).count();float ms;CU(cudaEventElapsedTime(&ms,start,stop));
    for(auto field:std::vector<std::pair<std::string,double*>>{{"vx",a.vx},{"vy",a.vy},{"vz",a.vz},{"p",a.p},{"rhs",a.b},{"truth",a.truth}})dump(prefix+"-"+field.first+".f64",field.second,g.n);
    std::cout<<std::setprecision(17)<<"{\"solver\":\""<<method<<"\",\"shape\":["<<g.nx<<","<<g.ny<<","<<g.nz<<"],\"lengths\":["<<g.lx<<","<<g.H<<","<<g.lz<<"],\"dt\":"<<dt<<",\"steps\":"<<steps<<",\"trial\":"<<argv[11]<<",\"setup_s\":"<<setup<<",\"elapsed_s\":"<<elapsed<<",\"event_s\":"<<ms/1000<<",\"pressure_seconds_per_simulated_second\":"<<elapsed/(dt*steps)<<",\"iterations\":[";
    for(size_t k=0;k<iterations.size();k++)std::cout<<(k?",":"")<<iterations[k];std::cout<<"]}\n";
    CU(cudaEventDestroy(start));CU(cudaEventDestroy(stop));if(plan)FT(cufftDestroy(plan));BL(cublasDestroy(handle));return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<"\n";return 1;}}
