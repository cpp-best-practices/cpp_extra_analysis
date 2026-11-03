cmake_minimum_required(VERSION 3.20)

project(cpp_extra_analysis LANGUAGES NONE)

option(CPP_EXTRA_ANALYSIS_REQUIRE_TOOLS "Fail configuration if an analysis tool is missing" OFF)

include(CTest)

find_package(Python3 3.9 REQUIRED COMPONENTS Interpreter)

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

foreach(test_case IN LISTS CHECK_TEST_CASES)
  file(RELATIVE_PATH test_name ${CMAKE_CURRENT_SOURCE_DIR}/checks ${test_case})
  string(REPLACE "/tests/" "/" test_name ${test_name})
  add_test(NAME ${test_name} COMMAND Python3::Interpreter ${HARNESS} ${test_case})
  set_tests_properties(${test_name} PROPERTIES ENVIRONMENT "${HARNESS_ENVIRONMENT}" SKIP_RETURN_CODE 77)
endforeach()

add_test(NAME harness.check_layout COMMAND Python3::Interpreter ${HARNESS} --list)
set_tests_properties(harness.check_layout PROPERTIES ENVIRONMENT PYTHONDONTWRITEBYTECODE=1)
