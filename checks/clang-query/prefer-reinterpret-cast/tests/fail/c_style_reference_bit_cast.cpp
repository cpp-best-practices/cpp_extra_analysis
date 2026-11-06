[[nodiscard]] float &reinterpret_bits(int &value)
{
  return (float &)value;// expect-finding
}
