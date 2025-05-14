cmake_minimum_required(VERSION 3.10)
project(chess_engine)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set Boost paths
set(BOOST_ROOT "D:/IT003/boost_1_88_0")
set(BOOST_INCLUDEDIR "${BOOST_ROOT}")
set(BOOST_LIBRARYDIR "${BOOST_ROOT}/lib64-msvc-14.3")

# Find Python
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Find Boost
set(Boost_USE_STATIC_LIBS OFF)
set(Boost_USE_MULTITHREADED ON)
set(Boost_USE_STATIC_RUNTIME OFF)
set(Boost_DEBUG ON)
find_package(Boost 1.88.0 REQUIRED COMPONENTS python)

# Include directories
include_directories(
    ${Python3_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS}
    ${BOOST_ROOT}
)

# Add the chess engine library
add_library(chess_engine SHARED
    chess_engine.cpp
)

# Link directories
link_directories(${BOOST_LIBRARYDIR})

# Link libraries
target_link_libraries(chess_engine
    ${Python3_LIBRARIES}
    ${Boost_LIBRARIES}
    boost_python3-vc143-mt-x64-1_88
)

# Set output directory
set_target_properties(chess_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}
    PREFIX ""
) 