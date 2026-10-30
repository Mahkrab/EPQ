"""Generate the independent Wendland audit from the validated cubic reader.

Only the kernel quadrature changes. Boundary volumes, units, energy and geometric
observables retain the same independent definitions used in the PBF frontier.
"""
from pathlib import Path
if __package__:
    from .frontier_dfsph_audit import generate
else:
    from frontier_dfsph_audit import generate


def wendland(destination:Path):
    generate(destination);source=destination.read_text()
    old_coefficient='const double coefficient=8/(std::acos(-1.)*h*h*h);'
    old_weight='auto weight=[&](double r2){double q=std::sqrt(r2)/h;return q>=1?0.:coefficient*(q<=.5?6*q*q*q-6*q*q+1:2*std::pow(1-q,3));};'
    if source.count(old_coefficient)!=1 or source.count(old_weight)!=1:raise ValueError('independent audit template changed')
    source=source.replace(old_coefficient,'const double coefficient=21/(2*std::acos(-1.)*h*h*h);').replace(old_weight,'auto weight=[&](double r2){double q=std::sqrt(r2)/h;return q>=1?0.:coefficient*std::pow(1-q,4)*(1+4*q);};')
    destination.write_text(source)


def unbounded(destination:Path,kernel='cubic'):
    if kernel=='wendland':wendland(destination)
    elif kernel=='cubic':generate(destination)
    else:raise ValueError('unsupported independent kernel')
    source=destination.read_text()
    changes=[('std::max(0.,double(p[i][1])-dx/2)','double(p[i][1])-dx/2'),
             ('std::min(upper[1],double(p[i][1])+dx/2)','double(p[i][1])+dx/2'),
             ('x>=0&&x<upper[0]&&z>=0&&z<upper[2]','std::isfinite(x)&&std::isfinite(z)')]
    for before,after in changes:
        if source.count(before)!=1:raise ValueError('volume audit template changed')
        source=source.replace(before,after)
    anchor='    std::map<Cell,std::vector<std::size_t>> grid;'
    if source.count(anchor)!=1:raise ValueError('audit search template changed')
    source=source.replace(anchor,'    for(auto point:p)for(float coordinate:point)if(std::abs(double(coordinate))>std::ldexp(pitch,40))throw std::runtime_error("unbounded audit coordinate exceeds representable volume domain");\n'+anchor)
    destination.write_text(source)
