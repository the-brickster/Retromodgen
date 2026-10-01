cmake_minimum_required(VERSION 3.22)
project(retromodgen_native LANGUAGES CXX)

add_library(retromodgen_native STATIC
    src/simplify.cpp
)

target_include_directories(retromodgen_native PUBLIC include)
target_compile_features(retromodgen_native PUBLIC cxx_std_20)
