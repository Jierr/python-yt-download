cmake_minimum_required(VERSION 3.22)
set(UNIT YoutubeDownloader)
project(${UNIT} LANGUAGES NONE)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

include(ExternalProject)

set(UPX_PACKAGE upx-4.0.2-win64.zip)
ExternalProject_Add(
    upx
    PREFIX "dependency"
    URL https://github.com/upx/upx/releases/download/v4.0.2/${UPX_PACKAGE}
    CONFIGURE_COMMAND ""
    BUILD_COMMAND ""
    INSTALL_COMMAND ""
)
set(UPX_DEPENDENCY_PATH "${CMAKE_BINARY_DIR}/dependency/src/upx/")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${UPX_DEPENDENCY_PATH}/${UPX_PACKAGE})


find_program(UPX upx
    HINTS "${UPX_DEPENDENCY_PATH}")
if(UPX)
    set(UPX_PATH ${UPX})
    cmake_path(REMOVE_FILENAME UPX_PATH)
    message(STATUS "UPX found: ${UPX}")
else()
    set(UPX_PATH ${UPX_DEPENDENCY_PATH})
    message(WARNING "UPX not found!")
    set(UBX )
endif()


set(SOURCE ytdownload.py)
add_custom_target(build-${UNIT}
    COMMAND pyinstaller --distpath "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}" 
    --specpath "${CMAKE_BINARY_DIR}/pyinstaller-spec" 
    --workpath "${CMAKE_BINARY_DIR}/pyinstaller" 
    -n ${UNIT} -F --clean --python-option u ${SOURCE}
    COMMENT "Create an executable cli program"
    USES_TERMINAL
    SOURCES ${SOURCE}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

    
add_custom_target(build-${UNIT}-with-upx
    COMMAND pyinstaller --distpath "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}"
    --specpath "${CMAKE_BINARY_DIR}/pyinstaller-spec" 
    --workpath "${CMAKE_BINARY_DIR}/pyinstaller" 
    --upx-dir "${UPX_PATH}"
    -n ${UNIT} -F --clean --python-option u ${SOURCE}
    COMMENT "Create an executable cli program"
    USES_TERMINAL
    VERBATIM
    SOURCES ${SOURCE}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    DEPENDS upx)

add_custom_target(cmake-upx-reconfigure
    #COMMAND ${CMAKE_COMMAND} -E rm -rf "CMakeCache.txt" "CMakeFiles"
    #COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --clean-first -t rebuild_cache
    COMMAND ${CMAKE_COMMAND} -E touch ${CMAKE_SOURCE_DIR}/CMakeLists.txt
    DEPENDS upx
)
