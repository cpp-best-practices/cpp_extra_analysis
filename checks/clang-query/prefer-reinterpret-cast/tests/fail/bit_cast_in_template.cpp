template<typename To, typename From> [[nodiscard]] To convert(const From value)
{
  return (To)value;// expect-finding
}

[[nodiscard]] const char *as_chars(const int *value) { return convert<const char *>(value); }
