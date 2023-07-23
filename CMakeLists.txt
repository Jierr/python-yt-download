cmake_minimum_required(VERSION 3.22)
set(UNIT YoutubeDownloader)
project(${UNIT} LANGUAGES NONE)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

set(SOURCE ytdownload.py)
add_custom_target(build-${UNIT}
    COMMAND pyinstaller --distpath "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}" 
    --specpath "${CMAKE_BINARY_DIR}" 
    --workpath "${CMAKE_BINARY_DIR}" 
    -n ${UNIT} -F --clean --python-option u ${SOURCE}
    COMMENT "Create an executable cli program"
    USES_TERMINAL
    SOURCES ${SOURCE}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})