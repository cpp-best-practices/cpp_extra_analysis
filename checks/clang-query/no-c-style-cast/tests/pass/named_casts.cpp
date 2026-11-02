#include <cstdint>

[[nodiscard]] constexpr int truncate(const double value) { return static_cast<int>(value); }

[[nodiscard]] std::uintptr_t address_of(const int &value)
{
  return reinterpret_cast<std::uintptr_t>(&value);
}
