"""Instrument a private native replay without changing the retained CUDA kernels.

Count the prediction-neighbour entries on every step and inspect pre-projection
residuals only in this diagnostic executable. Its deliberately expensive copies
and host quantiles are excluded from throughput claims.
"""
import argparse
from pathlib import Path


def generate(driver, output):
    source = driver.read_text()
    source = source.replace("std::uint64_t launches=0,waits=0,copies=0,copy_bytes=0;",
                            "std::uint64_t launches=0,waits=0,copies=0,copy_bytes=0,entry_sum=0;\n"
                            "    const bool collect_residuals=std::getenv(\"WORK_RESIDUALS\")!=nullptr;\n"
                            "    std::vector<std::uint64_t> entry_steps;\n"
                            "    std::vector<float> constraints(s.count);\n"
                            "    std::vector<Vector> corrections(s.count);\n"
                            "    std::ofstream residuals(prefix+\"-residuals.csv\");\n"
                            "    residuals << \"step,iteration,p95_compression,max_compression,max_correction_m\\n\";")
    source = source.replace("launch(12);launch(18", "entry_sum+=s.entries;entry_steps.push_back(s.entries);\n        launch(12);launch(18")
    source = source.replace("b.first_operation=9;launch(9);launch(10);packet();", """
            // The constraint belongs to positions before this correction. A
            // stopping rule may use it only after the preceding projection.
            if (collect_residuals) {
            checked(cudaMemcpy(constraints.data(),b.constraint,s.count*sizeof(float),cudaMemcpyDeviceToHost));
            checked(cudaMemcpy(corrections.data(),b.correction,s.count*sizeof(Vector),cudaMemcpyDeviceToHost));
            float largest_correction=0, largest_compression=0;
            for (unsigned i=0;i<s.count;++i) {
                constraints[i]=std::max(0.0f,constraints[i]);
                largest_compression=std::max(largest_compression,constraints[i]);
                auto v=corrections[i];
                largest_correction=std::max(largest_correction,std::sqrt(v.x*v.x+v.y*v.y+v.z*v.z));
            }
            const auto rank=static_cast<std::size_t>(.95*(s.count-1));
            std::nth_element(constraints.begin(),constraints.begin()+rank,constraints.end());
            residuals << step << ',' << iteration << ',' << constraints[rank] << ','
                      << largest_compression << ',' << largest_correction << '\\n';
            }
            b.first_operation=9;launch(9);launch(10);packet();""")
    source = source.replace('<<",\\\"last_neighbour_entries\\\":"<<actual',
                            '<<",\\\"last_neighbour_entries\\\":"<<actual\n'
                            '             <<",\\\"neighbour_entries_sum\\\":"<<entry_sum\n'
                            '             <<",\\\"jacobi_iterations\\\":"<<static_cast<std::uint64_t>(steps)*iterations')
    source = source.replace('std::cout<<"]}\\n";',
                            'std::cout<<"],\\\"neighbour_entries_per_step\\\":[";\n'
                            '    for (unsigned i=0;i<entry_steps.size();++i) std::cout<<(i?",":"")<<entry_steps[i];\n'
                            '    std::cout<<"]}\\n";')
    if "neighbour_entries_sum" not in source or "residuals << step" not in source:
        raise ValueError("native replay no longer matches the instrumentation boundary")
    output.write_text(source)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    generate(args.driver, args.output)
