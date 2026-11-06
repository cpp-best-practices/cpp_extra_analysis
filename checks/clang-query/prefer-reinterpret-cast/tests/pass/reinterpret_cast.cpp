[[nodiscard]] const unsigned char *object_bytes(const int &value)
{
  return reinterpret_cast<const unsigned char *>(&value);
}

[[nodiscard]] float &reinterpret_bits(int &value) { return reinterpret_cast<float &>(value); }
