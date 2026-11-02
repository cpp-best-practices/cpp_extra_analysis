[[nodiscard]] constexpr double sum(const int lhs, const float rhs)
{
  return (double)lhs// expect-finding
         + (double)rhs;// expect-finding
}

[[nodiscard]] constexpr unsigned to_unsigned(const int value) { return static_cast<unsigned>(value); }
