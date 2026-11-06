include_guard(GLOBAL)

include(CheckCXXCompilerFlag)

option(CPP_EXTRA_ANALYSIS_ENABLE_SANITIZERS "Build with AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(CPP_EXTRA_ANALYSIS_ENABLE_COVERAGE "Instrument the build for branch coverage (GCC)" OFF)

add_library(cpp_extra_analysis_options INTERFACE)

function(cpp_extra_analysis_add_supported_flag flag)
  string(MAKE_C_IDENTIFIER "CPP_EXTRA_ANALYSIS_HAS${flag}" supported)
  check_cxx_compiler_flag(${flag} ${supported})
  if(${supported})
    target_compile_options(cpp_extra_analysis_options INTERFACE ${flag})
  endif()
endfunction()

if(MSVC)
  target_compile_options(cpp_extra_analysis_options INTERFACE /W4 /permissive-)
  return()
endif()

target_compile_options(cpp_extra_analysis_options
                       INTERFACE -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wsign-conversion)

foreach(flag -fstack-protector-strong -fcf-protection -fstack-clash-protection)
  cpp_extra_analysis_add_supported_flag(${flag})
endforeach()

target_compile_definitions(cpp_extra_analysis_options INTERFACE _GLIBCXX_ASSERTIONS)

# _FORTIFY_SOURCE only works with optimisation, and toolchains may already define a lower level.
target_compile_options(cpp_extra_analysis_options
                       INTERFACE "$<$<CONFIG:Release,RelWithDebInfo,MinSizeRel>:-U_FORTIFY_SOURCE;-D_FORTIFY_SOURCE=3>")

if(CPP_EXTRA_ANALYSIS_ENABLE_SANITIZERS)
  target_compile_options(cpp_extra_analysis_options INTERFACE -fsanitize=address,undefined -fno-omit-frame-pointer)
  target_link_options(cpp_extra_analysis_options INTERFACE -fsanitize=address,undefined)
endif()

if(CPP_EXTRA_ANALYSIS_ENABLE_COVERAGE)
  target_compile_options(cpp_extra_analysis_options INTERFACE --coverage)
  target_link_options(cpp_extra_analysis_options INTERFACE --coverage)
endif()
