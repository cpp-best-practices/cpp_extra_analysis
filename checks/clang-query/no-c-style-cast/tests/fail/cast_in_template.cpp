template<typename To, typename From> [[nodiscard]] constexpr To convert(const From value)
{
  return (To)value;// expect-finding
}

[[nodiscard]] constexpr int use_convert() { return convert<int>(1.5); }
