template<typename To, typename From> [[nodiscard]] constexpr To convert(const From value)
{
  return (To)value;
}

[[nodiscard]] constexpr int truncate(const double value) { return convert<int>(value); }
