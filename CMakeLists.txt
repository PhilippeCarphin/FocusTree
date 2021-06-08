cmake_minimum_required(VERSION 3.16)

project(TEMPLATE C)

if("${CMAKE_INSTALL_PREFIX}" STREQUAL "/usr/local")
    set(CMAKE_INSTALL_PREFIX ${CMAKE_BINARY_DIR}/install-site CACHE FILEPATH "CMake Installation prefix for ${PROJECT_NAME}" FORCE)
    message(STATUS "Setting CMAKE_INSTALL_PREFIX to ${CMAKE_INSTALL_PREFIX}")
endif()

list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake/modules)

include(orgmanpages)
orgmanpages_add_man_target()

include(CTest)
add_custom_target(check COMMAND CTEST_OUTPUT_ON_FAILURE=true ${CMAKE_CTEST_COMMAND})

install(DIRECTORY bin/ DESTINATION bin USE_SOURCE_PERMISSIONS)
install(
    DIRECTORY libexec/
    DESTINATION libexec
    USE_SOURCE_PERMISSIONS
    PATTERN __pycache__ EXCLUDE
)
