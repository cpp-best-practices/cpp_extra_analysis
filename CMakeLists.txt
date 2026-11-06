cmake_minimum_required(VERSION 3.24)

project(cpp_extra_analysis LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(CPP_EXTRA_ANALYSIS_REQUIRE_TOOLS "Fail configuration if an analysis tool is missing" OFF)

include(CTest)
include(cmake/compiler_options.cmake)

find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)

set(CLANG_QUERY_NAMES clang-query)
set(CPPCHECK_NAMES cppcheck)
foreach(version RANGE 30 14 -1)
  list(APPEND CLANG_QUERY_NAMES clang-query-${version})
endforeach()

find_program(CLANG_QUERY_EXECUTABLE NAMES ${CLANG_QUERY_NAMES})
find_program(CPPCHECK_EXECUTABLE NAMES ${CPPCHECK_NAMES})

foreach(tool CLANG_QUERY CPPCHECK)
  if(${tool}_EXECUTABLE)
    message(STATUS "${tool}: ${${tool}_EXECUTABLE}")
  elseif(CPP_EXTRA_ANALYSIS_REQUIRE_TOOLS)
    message(FATAL_ERROR "${tool} not found; set ${tool}_EXECUTABLE")
  else()
    message(WARNING "${tool} not found; its checks will be skipped")
  endif()
endforeach()

include(cmake/static_analyzers.cmake)

set(HARNESS ${CMAKE_CURRENT_SOURCE_DIR}/tools/run_check_tests.py)
set(HARNESS_ENVIRONMENT
    PYTHONDONTWRITEBYTECODE=1
    CLANG_QUERY=${CLANG_QUERY_EXECUTABLE}
    CPPCHECK=${CPPCHECK_EXECUTABLE})

add_test(NAME harness.unit_tests
         COMMAND Python3::Interpreter -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/tests)
set_tests_properties(harness.unit_tests PROPERTIES ENVIRONMENT PYTHONDONTWRITEBYTECODE=1)

file(GLOB_RECURSE CHECK_TEST_CASES CONFIGURE_DEPENDS
     ${CMAKE_CURRENT_SOURCE_DIR}/checks/*/*/tests/pass/*.cpp
     ${CMAKE_CURRENT_SOURCE_DIR}/checks/*/*/tests/fail/*.cpp)

# Every test case must be valid, warning-free C++, or a check could pass on code the compiler rejects.
add_library(check_test_cases OBJECT ${CHECK_TEST_CASES})
target_link_libraries(check_test_cases PRIVATE cpp_extra_analysis_options)

foreach(test_case IN LISTS CHECK_TEST_CASES)
  file(RELATIVE_PATH test_name ${CMAKE_CURRENT_SOURCE_DIR}/checks ${test_case})
  string(REPLACE "/tests/" "/" test_name ${test_name})
  add_test(NAME ${test_name} COMMAND Python3::Interpreter ${HARNESS} ${test_case})
  set_tests_properties(${test_name} PROPERTIES ENVIRONMENT "${HARNESS_ENVIRONMENT}" SKIP_RETURN_CODE 77)
endforeach()

add_test(NAME harness.check_layout COMMAND Python3::Interpreter ${HARNESS} --list)
set_tests_properties(harness.check_layout PROPERTIES ENVIRONMENT PYTHONDONTWRITEBYTECODE=1)
