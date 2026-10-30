// Exploratory author-implementation comparison, outside Maelstrom and its clocks.
// Exact cubic kernels, geometric particle mass and sampled stationary walls.
#include "SPlisHSPlasH/Simulation.h"
#include "SPlisHSPlasH/DFSPH/TimeStepDFSPH.h"
#include "SPlisHSPlasH/BoundaryModel_Akinci2012.h"
#include "SPlisHSPlasH/RigidBodyObject.h"
#include "SPlisHSPlasH/TimeManager.h"
#include "Utilities/Logger.h"
#include "Utilities/Timing.h"
#include "Utilities/Counting.h"
#include <chrono>
#include <fstream>
#include <iostream>
#include <set>
using namespace SPH;
INIT_LOGGING
INIT_TIMING
INIT_COUNTING
struct Wall final:RigidBodyObject {
    Vector3r z=Vector3r::Zero();Quaternionr q=Quaternionr::Identity();std::vector<Vector3r> vertices;std::vector<unsigned> faces;
    bool isDynamic()const override{return false;} Real const getMass()const override{return 0;}
    Vector3r const&getPosition()const override{return z;}void setPosition(const Vector3r&)override{}
    Vector3r getWorldSpacePosition()const override{return z;}Vector3r const&getVelocity()const override{return z;}void setVelocity(const Vector3r&)override{}
    Quaternionr const&getRotation()const override{return q;}void setRotation(const Quaternionr&)override{}Matrix3r getWorldSpaceRotation()const override{return Matrix3r::Identity();}
    Vector3r const&getAngularVelocity()const override{return z;}void setAngularVelocity(const Vector3r&)override{}void addForce(const Vector3r&)override{}void addTorque(const Vector3r&)override{}void updateMeshTransformation()override{}
    const std::vector<Vector3r>&getVertices()const override{return vertices;}const std::vector<Vector3r>&getVertexNormals()const override{return vertices;}const std::vector<unsigned>&getFaces()const override{return faces;}
};
int main(int argc,char**argv)try{
    if(argc!=10)throw std::runtime_error("input.bin dt steps gx gy gz boxX,boxY,boxZ wall_spacing output_prefix");
    static_assert(sizeof(Real)==4);std::ifstream in(argv[1],std::ios::binary);unsigned n;in.read((char*)&n,4);in.seekg(96);
    std::vector<Vector3r> x(n),v(n);std::vector<unsigned> ids(n,0);
    for(auto*a:{&x,&v})for(auto&p:*a)for(int k=0;k<3;k++){float f;in.read((char*)&f,4);p[k]=f;}
    if(!in)throw std::runtime_error("input state incomplete");
    auto*sim=Simulation::getCurrent();sim->init(.025f,false);
    sim->setSimulationMethod((int)SimulationMethods::DFSPH);sim->setBoundaryHandlingMethod(BoundaryHandlingMethods::Akinci2012);
    sim->setKernel(Simulation::ENUM_KERNEL_CUBIC);sim->setGradKernel(Simulation::ENUM_GRADKERNEL_CUBIC);
    sim->setValue(Simulation::CFL_METHOD,Simulation::ENUM_CFL_NONE);sim->setValue(Simulation::ENABLE_Z_SORT,false);
    Vector3r gravity(std::stof(argv[4]),std::stof(argv[5]),std::stof(argv[6]));sim->setVecValue(Simulation::GRAVITATION,gravity.data());
    sim->addFluidModel("water",n,x.data(),v.data(),ids.data(),0);auto*f=sim->getFluidModel(0);
    f->setDensity0(1000);f->setViscosityMethod(0u);f->setVorticityMethod(0u);f->setSurfaceTensionMethod(0u);f->setDragMethod(0u);
    float bx,by,bz;if(std::sscanf(argv[7],"%f,%f,%f",&bx,&by,&bz)!=3)throw std::runtime_error("box required");
    double spacing=std::stod(argv[8]);BoundaryModel_Akinci2012*wall=nullptr;
    if(spacing>0){
        std::vector<Vector3r> points;std::set<std::array<int,3>> keys;std::array<int,3> max{int(std::lround(bx/spacing)),int(std::lround(by/spacing)),int(std::lround(bz/spacing))};
        for(int a=0;a<=max[0];a++)for(int b=0;b<=max[1];b++)for(int c=0;c<=max[2];c++)if(a==0||b==0||c==0||a==max[0]||b==max[1]||c==max[2])keys.insert({a,b,c});
        for(auto k:keys)points.emplace_back(k[0]*spacing,k[1]*spacing,k[2]*spacing);
        wall=new BoundaryModel_Akinci2012();wall->initModel(new Wall(),points.size(),points.data());sim->addBoundaryModel(wall);
    }
    auto*step=static_cast<TimeStepDFSPH*>(sim->getTimeStep());step->setValue(TimeStepDFSPH::MAX_ERROR,Real(.01));step->setValue(TimeStepDFSPH::MAX_ERROR_V,Real(.1));
    step->setValue(TimeStepDFSPH::MAX_ITERATIONS,100u);step->setValue(TimeStepDFSPH::MAX_ITERATIONS_V,100u);step->setValue(TimeStepDFSPH::MIN_ITERATIONS,2u);
    sim->setSimulationInitialized(true);if(wall)wall->deferredInit();sim->updateBoundaryVolume();step->resize();
    TimeManager::getCurrent()->setTimeStepSize(std::stof(argv[2]));
    std::string prefix=argv[9];std::ofstream observations(prefix+".jsonl");
    auto write=[&](unsigned k){std::ofstream out(prefix+"-"+std::to_string(k)+".bin",std::ios::binary);for(int field=0;field<2;field++)for(unsigned i=0;i<n;i++){Vector3r p=field?f->getVelocity(i):f->getPosition(i);for(int a=0;a<3;a++){float v=p[a];if(!std::isfinite(v))throw std::runtime_error("nonfinite state");out.write((char*)&v,4);}}};
    if(wall){std::ofstream out(prefix+"-boundary.bin",std::ios::binary);unsigned m=wall->numberOfParticles();out.write((char*)&m,4);for(unsigned i=0;i<m;i++){for(int a=0;a<3;a++){float value=wall->getPosition(i)[a];out.write((char*)&value,4);}float volume=wall->getVolume(i);out.write((char*)&volume,4);}}
    write(0);unsigned steps=std::stoul(argv[3]);double total=0;unsigned iterations=0,divergence=0;
    for(unsigned k=1;k<=steps;k++){auto start=std::chrono::steady_clock::now();step->step();double t=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();total+=t;auto i=step->getValue<unsigned>(TimeStepDFSPH::SOLVER_ITERATIONS),j=step->getValue<unsigned>(TimeStepDFSPH::SOLVER_ITERATIONS_V);iterations+=i;divergence+=j;observations<<"{\"step\":"<<k<<",\"solver_s\":"<<t<<",\"density_iterations\":"<<i<<",\"divergence_iterations\":"<<j<<"}\n";if(k==1||k%std::max(1u,unsigned(std::lround(.125/std::stof(argv[2]))))==0||k==steps)write(k);}
    std::cout<<"{\"particles\":"<<n<<",\"mass\":"<<f->getMass(0)<<",\"support\":"<<sim->getSupportRadius()<<",\"wall_particles\":"<<(wall?wall->numberOfParticles():0)<<",\"steps\":"<<steps<<",\"solver_s\":"<<total<<",\"density_iterations\":"<<iterations<<",\"divergence_iterations\":"<<divergence<<"}\n";
    delete sim;return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
