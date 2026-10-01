#include "retromodgen/simplify.hpp"

#include <stdexcept>

namespace retromodgen {

SimplifyResult simplify(
    std::span<const Vertex>,
    std::span<const Triangle>,
    const SimplifySettings&) {
    throw std::runtime_error("Weighted QEM simplifier not implemented yet");
}

} // namespace retromodgen
