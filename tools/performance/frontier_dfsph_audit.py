"""Build the independent cubic-kernel and sampled-wall DFSPH audit variant.

Only density quadrature differs from the production audit. Position, volume,
momentum and energy observables retain the same definitions and error budgets.
"""
import argparse
from pathlib import Path
import subprocess


def generate(destination):
    source=Path(__file__).with_name('frontier_quality.cpp').read_text()
    changes=[
        ('if(argc!=11)', 'if(argc!=12)'),
        ('const double coeff=315/(64*std::acos(-1.)*std::pow(h,9));', '''const double coefficient=8/(std::acos(-1.)*h*h*h);
    auto weight=[&](double r2){double q=std::sqrt(r2)/h;return q>=1?0.:coefficient*(q<=.5?6*q*q*q-6*q*q+1:2*std::pow(1-q,3));};
    std::map<Cell,std::vector<std::array<double,4>>> boundaries;
    if(std::string(argv[11])!="none") {std::ifstream b(argv[11],std::ios::binary);std::uint32_t m=0;b.read(reinterpret_cast<char*>(&m),4);for(unsigned j=0;j<m;j++){std::array<float,4>a;b.read(reinterpret_cast<char*>(a.data()),16);boundaries[cell({a[0],a[1],a[2]})].push_back({a[0],a[1],a[2],a[3]});}if(!b||b.peek()!=EOF)throw std::runtime_error("boundary state length differs");}'''),
        ('double density=coeff*std::pow(h*h,3)', 'double density=weight(0)'),
        ('auto found=grid.find({origin[0]+a,origin[1]+b,origin[2]+c});if(found==grid.end())continue;', '''auto key=Cell{origin[0]+a,origin[1]+b,origin[2]+c};auto boundary=boundaries.find(key);if(boundary!=boundaries.end())for(auto sample:boundary->second){double r2=0;for(int k=0;k<3;k++)r2+=(p[i][k]-sample[k])*(p[i][k]-sample[k]);density+=sample[3]*rest*weight(r2);}
            auto found=grid.find(key);if(found==grid.end())continue;'''),
        ('density+=coeff*std::pow(h*h-d2,3)', 'density+=weight(d2)')]
    for before,after in changes:
        if source.count(before)!=1:raise ValueError('audit template changed: '+before)
        source=source.replace(before,after)
    destination.write_text(source)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination',type=Path)
    a=p.parse_args()
    generate(a.destination)
    subprocess.run(['c++','-std=c++17','-O3','-Wall','-Wextra','-Werror',str(a.destination),'-o',str(a.destination.with_suffix(''))],check=True)
