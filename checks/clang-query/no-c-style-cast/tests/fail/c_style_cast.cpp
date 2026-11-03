[[nodiscard]] constexpr int truncate(const double value)
{
  return (int)value;// expect-finding
}
