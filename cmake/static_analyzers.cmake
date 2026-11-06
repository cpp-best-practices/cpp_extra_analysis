include_guard(GLOBAL)

option(CPP_EXTRA_ANALYSIS_ENABLE_CLANG_TIDY "Run clang-tidy on every C++ source as it compiles" OFF)
option(CPP_EXTRA_ANALYSIS_ENABLE_CPPCHECK "Run cppcheck on every C++ source as it compiles" OFF)

if(CPP_EXTRA_ANALYSIS_ENABLE_CLANG_TIDY)
  set(CLANG_TIDY_NAMES clang-tidy)
  foreach(version RANGE 30 14 -1)
    list(APPEND CLANG_TIDY_NAMES clang-tidy-${version})
  endforeach()
  find_program(CLANG_TIDY_EXECUTABLE NAMES ${CLANG_TIDY_NAMES} REQUIRED)
  set(CMAKE_CXX_CLANG_TIDY ${CLANG_TIDY_EXECUTABLE})
endif()

if(CPP_EXTRA_ANALYSIS_ENABLE_CPPCHECK)
  find_program(CPPCHECK_EXECUTABLE NAMES cppcheck REQUIRED)
  set(CMAKE_CXX_CPPCHECK
      ${CPPCHECK_EXECUTABLE}
      --enable=warning,style,performance,portability
      --inline-suppr
      --error-exitcode=2
      --std=c++20)
endif()
