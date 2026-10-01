#pragma once

#include <cstdint>
#include <span>
#include <vector>

namespace retromodgen {

struct Vertex {
    float x{};
    float y{};
    float z{};
};

struct Triangle {
    std::uint32_t a{};
    std::uint32_t b{};
    std::uint32_t c{};
};

struct SimplifySettings {
    std::uint32_t target_triangles{};
    float silhouette_weight{4.0F};
    float sharp_edge_weight{2.0F};
    float uv_seam_weight{2.0F};
};

struct SimplifyResult {
    std::vector<Vertex> vertices;
    std::vector<Triangle> triangles;
};

// Phase 2: weighted QEM simplifier. Start with a scalar correctness-first implementation.
SimplifyResult simplify(
    std::span<const Vertex> vertices,
    std::span<const Triangle> triangles,
    const SimplifySettings& settings);

} // namespace retromodgen
