cmake_minimum_required(VERSION 3.10)

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


add_custom_command(
    OUTPUT go-ftserver
    COMMAND go build ${CMAKE_SOURCE_DIR}/goftserver/main.go && mv main ${CMAKE_BINARY_DIR}/go-ftserver
    DEPENDS ${CMAKE_SOURCE_DIR}/focus/focus.go;${CMAKE_SOURCE_DIR}/goftserver/main.go
)
add_custom_target(goftserver ALL DEPENDS go-ftserver)

install(
    DIRECTORY share/FocusTree/clients/basic_js_client/
    DESTINATION share/FocusTree/clients/basic_js_client
    USE_SOURCE_PERMISSIONS
)

install(DIRECTORY bin/ DESTINATION bin USE_SOURCE_PERMISSIONS)
install(PROGRAMS ${CMAKE_BINARY_DIR}/go-ftserver DESTINATION bin)
install(
    DIRECTORY libexec/
    DESTINATION libexec
    USE_SOURCE_PERMISSIONS
    PATTERN __pycache__ EXCLUDE
)
