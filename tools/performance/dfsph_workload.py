"""Count PBF row-entry visits in a separately matched native replay.

The retained prefix reuse leaves one full density/owner pass, one half suffix
pass and one full correction pass per Jacobi iteration. Prediction neighbours
are symmetric, so the exact total is 5E/2 per iteration. Replay clocks are ignored.
"""
import argparse
from pathlib import Path


def generate(destination):
    source=Path(__file__).with_name('frontier_driver.cu').read_text()
    source=source.replace('#include "kernels.cu"','#include "../../native/kernels.cu"')
    anchor='    std::vector<double> durations;'
    if source.count(anchor)!=1:raise ValueError('PBF driver template changed')
    source=source.replace(anchor,anchor+'\n    std::ofstream workload(prefix+"-workload.jsonl");workload.precision(17);')
    anchor='        durations.push_back(seconds(start));'
    if source.count(anchor)!=1:raise ValueError('PBF step observer changed')
    source=source.replace(anchor,anchor+'''\n        if(s.entries%2)throw std::runtime_error("prediction neighbourhood lost symmetry");
        workload<<"{\\"step\\":"<<step<<",\\"dt\\":"<<s.timestep<<",\\"jacobi_iterations\\":"<<iterations<<",\\"fluid_neighbour_entries\\":"<<s.entries<<",\\"row_entry_visits\\":"<<s.entries*iterations*5/2<<",\\"row_sweeps\\":"<<2.5*iterations<<",\\"search_count_fill_passes\\":2}\\n";''')
    destination.write_text(source)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path);generate(p.parse_args().destination)
