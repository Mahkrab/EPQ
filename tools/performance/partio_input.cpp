// Read imported comparator geometry through its actual Partio parser. The JSON
// round trip lets the independent Python check compare binary32 coordinates.
#include <Partio.h>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>

struct ReleaseParticles {
    void operator()(Partio::ParticlesDataMutable *particles) const { particles->release(); }
};

int main(int argc, char **argv) {
    if (argc != 2) {
        std::cerr << "expected one particle input file\n";
        return 2;
    }
    std::unique_ptr<Partio::ParticlesDataMutable, ReleaseParticles> particles(Partio::read(argv[1]));
    Partio::ParticleAttribute position;
    if (!particles || !particles->attributeInfo("position", position) || position.count != 3 ||
        (position.type != Partio::VECTOR && position.type != Partio::FLOAT)) {
        std::cerr << "particle input has no three-component position attribute\n";
        return 3;
    }
    std::cout << std::setprecision(std::numeric_limits<float>::max_digits10)
              << "{\"count\":" << particles->numParticles() << ",\"positions\":[";
    for (int i = 0; i < particles->numParticles(); ++i) {
        const auto *point = particles->data<float>(position, i);
        for (int axis = 0; axis < 3; ++axis) {
            if (!std::isfinite(point[axis])) {
                std::cerr << "non-finite imported coordinate\n";
                return 3;
            }
        }
        if (i) std::cout << ',';
        std::cout << '[' << point[0] << ',' << point[1] << ',' << point[2] << ']';
    }
    std::cout << "]}\n";
    return std::cout ? 0 : 4;
}
